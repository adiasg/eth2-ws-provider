# Eth2 Weak Subjectivity Provider Server

This repo contains a simple Eth2 [weak subjectivity](https://github.com/ethereum/eth2.0-specs/blob/dev/specs/phase0/weak-subjectivity.md) provider server.

## Prerequisites
- Docker Engine
- Docker Compose

## Launching the server
1. Build the containers:
  - Copy `./default.env` to `./.env` and fill in your `ETH2_API`
  - Build the docker image:
  ```bash
  docker-compose build
  ```
2. Run the server on the standard HTTP port `80`:
  ```bash
  docker-compose up
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
