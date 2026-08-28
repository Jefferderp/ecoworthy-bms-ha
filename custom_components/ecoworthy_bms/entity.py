"""Shared battery entity model."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EcoWorthyCoordinator


class EcoWorthyEntity(CoordinatorEntity[EcoWorthyCoordinator]):
    """An entity backed only by coordinator memory."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: EcoWorthyCoordinator, mac: str, key: str) -> None:
        super().__init__(coordinator, context=mac)
        self.mac = mac
        self._attr_unique_id = f"{mac.replace(':', '').lower()}_{key}"

    @property
    def battery(self) -> dict[str, Any]:
        return self.coordinator.data["batteries"].get(self.mac, {})

    @property
    def available(self) -> bool:
        return super().available and bool(self.battery.get("available"))

    @property
    def device_info(self) -> DeviceInfo:
        identity = self.battery.get("identity", {})
        info = identity.get("device_info", {})
        name = identity.get("name") or identity.get("advertised_name") or self.mac
        return DeviceInfo(
            identifiers={(DOMAIN, self.mac)},
            connections={(CONNECTION_BLUETOOTH, self.mac)},
            name=name,
            manufacturer="ECO-WORTHY",
            model=info.get("hw_version")
            or identity.get("advertised_name")
            or identity.get("driver"),
            sw_version=info.get("sw_version"),
        )
