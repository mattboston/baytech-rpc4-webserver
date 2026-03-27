# Baytech RPC-4 PDU Webserver

The Baytech RPC-4 (at least the one I have) is an 8 port PDU and you can remotely switch on and off individual ports.  But it has to be managed over a console cable. This project uses a Raspberry Pi, USB to Serial adapter, and a Cisco console cable and gives you a web interface to manage the Baytech RPC-4 PDU.

## Features

- Web UI to view outlet status, toggle power, and rename outlets
- REST API for programmatic control
- Home Assistant custom integration (see `homeassistant/`)
- Thread-safe serial access — safe for concurrent requests

## Configuration

Copy `config.ini.example` to `config.ini` and set:

| Key | Description |
|---|---|
| `device` | Serial device path (e.g. `/dev/ttyUSB0`) |
| `api_key` | Secret key required for all API requests |
| `log_file` | Path to log file |
| `debug` | `true` / `false` |

## API

All API endpoints require the header `X-API-Key: <your-key>`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/status` | Returns state of all outlets |
| `GET` | `/api/status/{port_id}` | Returns state of a single outlet |
| `POST` | `/api/power/{port_id}` | Toggles outlet on/off |
| `POST` | `/api/port/rename/{port_id}` | Renames an outlet — body: `{"name": "new-name"}` (max 10 chars) |
