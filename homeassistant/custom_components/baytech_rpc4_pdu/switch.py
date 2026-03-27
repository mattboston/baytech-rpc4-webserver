"""PDU switch entities — one per outlet."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PduCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PduCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PduOutletSwitch(coordinator, port_id, entry.entry_id)
        for port_id in coordinator.data
    )


class PduOutletSwitch(CoordinatorEntity, SwitchEntity):
    """Represents a single PDU outlet as a HA switch."""

    def __init__(self, coordinator: PduCoordinator, port_id: int, entry_id: str) -> None:
        super().__init__(coordinator)
        self._port_id = port_id
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_outlet_{port_id}"

    @property
    def _outlet(self) -> dict:
        return self.coordinator.data.get(self._port_id, {})

    @property
    def name(self) -> str:
        return self._outlet.get("name", f"Outlet {self._port_id}")

    @property
    def is_on(self) -> bool:
        return self._outlet.get("state", "Off").lower() == "on"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="PDU Power Controller",
            manufacturer="PDU",
        )

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_outlet(self._port_id, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_outlet(self._port_id, False)
