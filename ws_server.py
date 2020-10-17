import httpx
import os
from eth2spec.phase0.spec import *
from flask import Flask, jsonify
app = Flask(__name__)

# If running this server on your host machine (outside of docker), then
# run `export ETH2_API=<your Eth2 API endpoint>` before launching this server
ETH2_API = os.environ['ETH2_API']

def get_json(url):
    response = httpx.get(url)
    if response.status_code != 200:
        raise Exception(f"GET {url} returned with status code {response.status_code}")
    return response.json()

def get_finalized_checkpoint():
    finality_checkpoints = get_json(ETH2_API + '/eth/v1/beacon/states/finalized/finality_checkpoints')
    finalized_checkpoint = finality_checkpoints["data"]["finalized"]
    return finalized_checkpoint

def get_current_slot():
    head = get_json(ETH2_API + '/eth/v1/beacon/headers/head')
    slot = head["data"]["header"]["message"]["slot"]
    return int(slot)

def get_active_validator_count_at_finalized():
    validators = get_json(ETH2_API + f'/eth/v1/beacon/states/finalized/validators')
    active_validator_count = 0
    for v in validators["data"]:
        if type(v["status"]) == str and v["status"].lower().startswith("active"):
            active_validator_count += 1
    return active_validator_count

def compute_weak_subjectivity_period(validator_count) -> uint64:
    weak_subjectivity_period = MIN_VALIDATOR_WITHDRAWABILITY_DELAY
    if validator_count >= MIN_PER_EPOCH_CHURN_LIMIT * CHURN_LIMIT_QUOTIENT:
        weak_subjectivity_period += SAFETY_DECAY * CHURN_LIMIT_QUOTIENT // (2 * 100)
    else:
        weak_subjectivity_period += SAFETY_DECAY * validator_count // (2 * 100 * MIN_PER_EPOCH_CHURN_LIMIT)
    return weak_subjectivity_period

def get_ws_checkpoint_data():
    finalized_checkpoint = get_finalized_checkpoint()
    active_validator_count = get_active_validator_count_at_finalized()
    ws_period = compute_weak_subjectivity_period(active_validator_count)
    current_slot = get_current_slot()
    current_epoch = compute_epoch_at_slot(current_slot)
    finalized_epoch = int(finalized_checkpoint["epoch"])
    current_epoch_in_ws_period = (current_epoch - finalized_epoch < ws_period)

    return {
        "current_epoch": current_epoch,
        "ws_checkpoint": f'{finalized_checkpoint["root"]}:{finalized_epoch}',
        "ws_period": ws_period,
        "is_safe": current_epoch_in_ws_period
    }

@app.route('/')
def serve_ws_data():
    return jsonify(get_ws_checkpoint_data())
