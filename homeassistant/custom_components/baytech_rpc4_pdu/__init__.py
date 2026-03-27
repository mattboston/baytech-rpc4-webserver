"""PDU Power Controller integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_API_KEY, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PDU from a config entry."""
    host = entry.data[CONF_HOST].rstrip("/")
    api_key = entry.data[CONF_API_KEY]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    session = async_get_clientsession(hass)

    coordinator = PduCoordinator(hass, session, host, api_key, scan_interval)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(f"Unable to connect to PDU at {host}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


class PduCoordinator(DataUpdateCoordinator):
    """Coordinator that polls the PDU /api/status endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        host: str,
        api_key: str,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._session = session
        self.host = host
        self._headers = {"X-API-Key": api_key}

    async def _async_update_data(self) -> dict:
        """Fetch outlet states from the PDU."""
        url = f"{self.host}/api/status"
        try:
            async with self._session.get(url, headers=self._headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with PDU: {err}") from err

        # Flatten outlets: {port_id: {"name": ..., "state": "On"/"Off"}}
        outlets = {}
        for port_id_str, outlet_dict in data.get("outlets", {}).items():
            port_id = int(port_id_str)
            name, state = next(iter(outlet_dict.items()))
            outlets[port_id] = {"name": name, "state": state}

        return outlets

    async def async_toggle_outlet(self, port_id: int) -> None:
        """POST to toggle the outlet state."""
        url = f"{self.host}/api/power/{port_id}"
        async with self._session.post(url, headers=self._headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()

    async def async_set_outlet(self, port_id: int, turn_on: bool) -> None:
        """Set outlet to a desired state, toggling only if needed."""
        current = self.data.get(port_id, {}).get("state", "").lower()
        is_on = current == "on"
        if turn_on != is_on:
            await self.async_toggle_outlet(port_id)
        await self.async_request_refresh()
