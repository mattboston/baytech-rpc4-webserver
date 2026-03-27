"""Config flow for PDU integration."""
from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, DEFAULT_SCAN_INTERVAL, DOMAIN

STEP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="http://192.168.1.x"): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=5)
        ),
    }
)


class PduConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PDU."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].rstrip("/")
            session = async_get_clientsession(self.hass)
            api_key = user_input[CONF_API_KEY]
            try:
                async with session.get(
                    f"{host}/api/status",
                    headers={"X-API-Key": api_key},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    resp.raise_for_status()
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"PDU ({host})",
                    data={**user_input, CONF_HOST: host},
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_SCHEMA, errors=errors
        )
