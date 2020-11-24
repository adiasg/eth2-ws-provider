import httpx
from eth2spec.phase0.spec import (
    compute_epoch_at_slot,
    CHURN_LIMIT_QUOTIENT, MIN_PER_EPOCH_CHURN_LIMIT,
    MIN_VALIDATOR_WITHDRAWABILITY_DELAY, SAFETY_DECAY, SECONDS_PER_SLOT
)
from flask import Flask, jsonify
import redis
import time
import json
import logging
import yaml

with open("/app/config.yml", "r") as config_file:
    cfg = yaml.safe_load(config_file)
logging.basicConfig(format='%(asctime)s -- %(levelname)s -- %(message)s')
logging.getLogger().setLevel(logging.INFO)
r = redis.Redis(host='redis')
# ETH2_API is the Eth2 beacon node's HTTP endpoint
ETH2_API = cfg["eth2_api"]
# MIN_CACHE_UPDATE_EPOCHS is the minimum number of epochs between consecutive
# updates of the cached weak subjectivity data
MIN_CACHE_UPDATE_EPOCHS = int(cfg["min_cache_update_epochs"])
# Optional graffiti to serve in the HTTP JSON response
WS_SERVER_GRAFFITI = cfg["ws_server_graffiti"]


def query_eth2_api(endpoint):
    url = ETH2_API + endpoint
    response = httpx.get(url, timeout=100)
    if response.status_code != 200:
        raise Exception(
            f"GET {url} returned with status code {response.status_code}"
            f" and message {response.json()['message']}"
        )
    return response.json()


def get_current_epoch():
    genesis_time_cache = r.get('genesis_time')
    if genesis_time_cache is None:
        genesis = query_eth2_api('/eth/v1/beacon/genesis')
        genesis_time = int(genesis["data"]["genesis_time"])
        r.set('genesis_time', genesis_time)
    else:
        genesis_time = int(genesis_time_cache.decode('utf-8'))
    current_slot = (time.time() - genesis_time) // SECONDS_PER_SLOT
    return compute_epoch_at_slot(int(current_slot))


def get_finalized_checkpoint():
    finality_checkpoints = query_eth2_api(
        '/eth/v1/beacon/states/finalized/finality_checkpoints'
        )
    finalized_checkpoint = finality_checkpoints["data"]["finalized"]
    return finalized_checkpoint


def get_state_root_at_block(block_root):
    block = query_eth2_api(f'/eth/v1/beacon/blocks/{block_root}')
    return block["data"]["message"]["state_root"]


def get_active_validator_count_at_finalized():
    validators = query_eth2_api('/eth/v1/beacon/states/finalized/validators')
    active_validator_count = 0
    for v in validators["data"]:
        is_active_validator = (
            type(v["status"]) == str
            and v["status"].lower().startswith("active")
        )
        if is_active_validator:
            active_validator_count += 1
    return active_validator_count


def get_active_validator_count_at_state(state_root):
    validators = query_eth2_api(
        f'/eth/v1/beacon/states/{state_root}/validators'
    )
    active_validator_count = 0
    for v in validators["data"]:
        is_active_validator = (
            type(v["status"]) == str
            and v["status"].lower().startswith("active")
        )
        if is_active_validator:
            active_validator_count += 1
    return active_validator_count


def compute_weak_subjectivity_period(validator_count):
    # Compute the weak subjectivity period as described in eth2.0-specs:
    # https://github.com/ethereum/eth2.0-specs/blob/dev/specs/phase0/weak-subjectivity.md#calculating-the-weak-subjectivity-period
    weak_subjectivity_period = MIN_VALIDATOR_WITHDRAWABILITY_DELAY
    if validator_count >= MIN_PER_EPOCH_CHURN_LIMIT * CHURN_LIMIT_QUOTIENT:
        weak_subjectivity_period += (
            (SAFETY_DECAY * CHURN_LIMIT_QUOTIENT) // (2 * 100)
        )
    else:
        weak_subjectivity_period += (
            (SAFETY_DECAY * validator_count)
            // (2 * 100 * MIN_PER_EPOCH_CHURN_LIMIT)
        )
    return weak_subjectivity_period


def atomic_get_finalized_checkpoint_and_validator_count():
    finalized_checkpoint = get_finalized_checkpoint()
    finalized_epoch = int(finalized_checkpoint["epoch"])
    active_validator_count = get_active_validator_count_at_finalized()
    # Re-check finalized_checkpoint to see if it changed between the last two
    # API calls
    now_finalized_checkpoint = get_finalized_checkpoint()
    now_finalized_epoch = int(now_finalized_checkpoint["epoch"])
    if now_finalized_epoch != finalized_epoch:
        return atomic_get_finalized_checkpoint_and_validator_count()

    return finalized_checkpoint, active_validator_count


def update_ws_data_cache():
    logging.info(f'Fetching weak subjectivity data from {ETH2_API}')
    finalized_checkpoint, active_validator_count = \
        atomic_get_finalized_checkpoint_and_validator_count()
    finalized_epoch = int(finalized_checkpoint["epoch"])
    finalized_block_root = finalized_checkpoint["root"]
    ws_period = compute_weak_subjectivity_period(active_validator_count)
    ws_data = {
        "finalized_epoch": finalized_epoch,
        "ws_checkpoint": f'{finalized_block_root}:{finalized_epoch}',
        "ws_period": ws_period,
    }
    current_epoch = get_current_epoch()
    ws_data_cache = {
        "caching_epoch": current_epoch,
        "ws_data": ws_data
    }
    logging.info(
        f"Updating redis cache key 'ws_data_cache' with {ws_data_cache}"
    )
    r.set('ws_data_cache', json.dumps(ws_data_cache))
    return ws_data


def get_ws_data():
    ws_data_cache_bytes = r.get('ws_data_cache')
    # If redis cache is empty, initialize it
    if ws_data_cache_bytes is None:
        logging.debug(
            "No 'ws_data_cache' in cache. Initializing cache now."
        )
        return update_ws_data_cache()
    ws_data_cache = json.loads(ws_data_cache_bytes.decode('utf-8'))
    logging.debug(
        f"Got from redis cache for key 'ws_data_cache': {ws_data_cache}"
    )
    # Refresh redis cache if it has been more than MIN_CACHE_UPDATE_EPOCHS
    # since last update
    current_epoch = get_current_epoch()
    cache_expired = (
        current_epoch - ws_data_cache["caching_epoch"]
        > MIN_CACHE_UPDATE_EPOCHS
    )
    if cache_expired:
        logging.debug(
            "Cached value for 'ws_data_cache' has expired - "
            f"ws_data_cache: {ws_data_cache}, current epoch: {current_epoch}"
        )
        return update_ws_data_cache()
    ws_data = ws_data_cache["ws_data"]
    # Refresh redis cache if the current epoch is outside of the WS safety
    # period since last update
    current_epoch_in_ws_period = (
        current_epoch - ws_data["finalized_epoch"] < ws_data["ws_period"]
    )
    if not current_epoch_in_ws_period:
        logging.info(
            "Cached value for 'ws_data_cache' is unsafe - "
            f"ws_data_cache: {ws_data_cache}, current epoch: {current_epoch}"
        )
        return update_ws_data_cache()
    return ws_data


def prepare_response():
    ws_data = get_ws_data()
    current_epoch = get_current_epoch()
    current_epoch_in_ws_period = (
        current_epoch - ws_data["finalized_epoch"] < ws_data["ws_period"]
    )
    response = {
        "current_epoch": current_epoch,
        "ws_checkpoint": ws_data["ws_checkpoint"],
        "ws_period": ws_data["ws_period"],
        "is_safe": current_epoch_in_ws_period
    }
    if WS_SERVER_GRAFFITI:
        response['graffiti'] = WS_SERVER_GRAFFITI
    return response


# Update redis cache on startup
logging.info("Initializing cache. Server will be ready soon.")
get_current_epoch()
update_ws_data_cache()
logging.info("Cache initialized. Ready to serve requests.")

app = Flask(__name__)


@app.route('/')
def serve_ws_data():
    return jsonify(prepare_response())
