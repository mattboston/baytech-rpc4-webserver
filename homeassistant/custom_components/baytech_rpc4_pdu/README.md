# PDU Power Controller

A Home Assistant custom integration for controlling a PDU (Power Distribution Unit) with 8 individually switchable outlets via a local HTTP API.

## Features

- Displays the on/off state of all 8 outlets as switch entities
- Turn individual outlets on or off from the HA UI, automations, or scripts
- All outlets are polled in a single API call for efficiency
- Outlet names are read from the PDU and used as entity names

## Requirements

- The PDU must be reachable from your Home Assistant host over HTTP
- No additional Python packages required (uses HA's built-in aiohttp)

## Installation

1. Copy the `baytech_rpc4_pdu/` folder into your HA configuration directory:
   ```
   config/custom_components/baytech_rpc4_pdu/
   ```
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**.
4. Search for **PDU Power Controller** and follow the setup wizard.

## Configuration

The integration is configured through the UI. You will be prompted for:

| Field | Description | Default |
| --- | --- | --- |
| Host URL | Full URL to your PDU (e.g. `http://192.168.1.100`) | — |
| API Key | Secret key configured on the PDU webserver | — |
| Poll interval | How often to refresh outlet states, in seconds | `180` |

## Entities

Each outlet is exposed as a `switch` entity. Entity names are taken from the outlet names configured on the PDU. All 8 switches are grouped under a single **PDU Power Controller** device.

Example entities after setup:

```
switch.unused1
switch.unused2
...
switch.unused8
```

Rename outlets via the PDU web UI or `POST /api/port/rename/{port_id}`. HA entity names update on the next poll.

## API Reference

This integration uses the following PDU endpoints:

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/status` | Returns state of all outlets (polled on interval) |
| `POST` | `/api/power/{port_id}` | Toggles the outlet state |
| `POST` | `/api/port/rename/{port_id}` | Renames an outlet — body: `{"name": "new-name"}` (max 10 chars) |

The integration reads current state before toggling to ensure idempotent on/off commands — if an outlet is already in the desired state, no API call is made.
