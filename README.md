# Eth2 Weak Subjectivity Provider Server

This repo contains a simple Eth2 [weak subjectivity](https://github.com/ethereum/eth2.0-specs/blob/dev/specs/phase0/weak-subjectivity.md) provider server.

## Prerequisites
- Docker Engine & Docker Compose
- Eth2 beacon node with accessible HTTP API
- Accurate system time

## Launching the server
1. Build the containers:
  - Copy `./default.env` to `./.env` and fill in your `ETH2_API` in `./.env`
  - Build the docker image using: `docker-compose build`
2. Run the server using: `docker-compose up`.

#### Advanced Configuration:
- The default port is `80`. This may be changed by editing the port mapping for `eth2_ws_server` in `docker-compose.yml`.
- This application uses the `uwsgi` Python server. For advanced settings of `uwsgi`, load the desired configuration (such as number of processes & threads) in the `uwsgi_config.ini` file

#### Using a Eth2 Beacon Node running in a Docker container
If your Eth2 beacon node is running inside a Docker container on the same machine, you will have to use the pre-existing Docker network to connect to the beacon node:
- Find the name of the pre-existing Docker network that your Eth2 beacon node container is using. This will be the top-level JSON key returned by: `docker inspect <NAME_OF_CONTAINER> -f "{{json .NetworkSettings.Networks}}"`
- In `docker-compose.yml`, uncomment the `networks` section and enter the name of the pre-existing Docker network in the `name` entry.

## User guide

The Eth2 WS server will serve the following data in JSON format:
- `current_epoch`: The current epoch number of the Eth2 network
- `is_safe`: A boolean value representing whether the Eth2 API endpoint used was operating under safe WS conditions, i.e., if the current epoch is within the safe WS period of the WS checkpoint that is provided in this response
- `ws_checkpoint`: The WS checkpoint in `block_root:epoch_number` format
- `ws_period`: The WS period as [calculated](https://github.com/ethereum/eth2.0-specs/blob/dev/specs/phase0/weak-subjectivity.md#calculating-the-weak-subjectivity-period) for the state at the WS checkpoint that is provided in this response
- `graffiti`: Optional graffiti set by the server operator

Example:
```json
{
  "current_epoch":16552,
  "is_safe":true,
  "ws_checkpoint":"0xe8e4b0170c4b9bfb09e477c754db0f5a02756859ccf1e834a39dbafbe9292f3c:15601",
  "ws_period":1188,
  "graffiti": "This is an Eth2 weak subjectivity data server"
}
```
