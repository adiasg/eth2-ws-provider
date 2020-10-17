# Eth2 Weak Subjectivity Provider Server

This repo contains a simple Eth2 [weak subjectivity](https://github.com/ethereum/eth2.0-specs/blob/dev/specs/phase0/weak-subjectivity.md) provider server.

## Prerequisites
- Python 3.8 or higher
- An [Eth2 API endpoint](https://ethereum.github.io/eth2.0-APIs/)
<!-- - Docker (if you want to run this as Docker instance) -->

## Launching the server
<!-- ### Running as a Docker instance

- Fill in `ETH2_API` with your Eth2 API endpoint
- Build the docker image:
```bash
docker build -t eth2-ws-server .
```
- Run as a docker instance:
```bash
sudo docker run -p 80:80 eth2-ws-server
``` -->

### Running on host machine

- Run the makefile to install all dependencies in a venv:
```bash
make install
```
- Provide your Eth2 API endpoint by running:
```bash
export ETH2_API=<your Eth2 API endpoint>
```
- Activate the venv and run the server:
```bash
. venv/bin/activate
uwsgi --http 0.0.0.0:9090 --wsgi ws_server:app
```


## User guide

The Eth2 WS server will serve the following data in JSON format:
- `current_epoch`: The current epoch number of the Eth2 network
- `is_safe`: A boolean value representing whether the Eth2 API endpoint used was operating under safe WS conditions, i.e., if the current epoch is within the safe WS period of the WS checkpoint that is provided in this response
- `ws_checkpoint`: The WS checkpoint in `block_root:epoch_number` format
- `ws_period`: The [WS period as calculated](https://github.com/ethereum/eth2.0-specs/blob/dev/specs/phase0/weak-subjectivity.md#calculating-the-weak-subjectivity-period) for the state at the WS checkpoint that is provided in this response

Example:
```json
{
  "current_epoch":16552,
  "is_safe":true,
  "ws_checkpoint":"0xe8e4b0170c4b9bfb09e477c754db0f5a02756859ccf1e834a39dbafbe9292f3c:15601",
  "ws_period":1188
}
```
