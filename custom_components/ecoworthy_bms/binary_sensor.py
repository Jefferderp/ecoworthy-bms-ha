"""Binary sensors for EcoWorthy BMS Gateway."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.entity import EntityCategory

from . import EcoWorthyConfigEntry
from .entity import EcoWorthyEntity


@dataclass(frozen=True, kw_only=True)
class BMSBinaryDescription(BinarySensorEntityDescription):
    section: str = "telemetry"


BINARY_SENSORS = (
    BMSBinaryDescription(
        key="problem",
        translation_key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BMSBinaryDescription(
        key="battery_charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    BMSBinaryDescription(
        key="chrg_mosfet",
        translation_key="charge_mosfet",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    BMSBinaryDescription(
        key="dischrg_mosfet",
        translation_key="discharge_mosfet",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass, entry: EcoWorthyConfigEntry, async_add_entities
) -> None:
    coordinator = entry.runtime_data
    known: set[tuple[str, str]] = set()

    def discover_entities() -> None:
        entities = []
        for mac, battery in coordinator.data["batteries"].items():
            connectivity_id = (mac, "connectivity")
            if connectivity_id not in known:
                known.add(connectivity_id)
                entities.append(EcoWorthyConnectivitySensor(coordinator, mac))
            telemetry = battery.get("telemetry", {})
            for description in BINARY_SENSORS:
                identity = (mac, description.key)
                if description.key in telemetry and identity not in known:
                    known.add(identity)
                    entities.append(
                        EcoWorthyBinarySensor(coordinator, mac, description)
                    )
        if entities:
            async_add_entities(entities)

    discover_entities()
    entry.async_on_unload(coordinator.async_add_listener(discover_entities))


class EcoWorthyBinarySensor(EcoWorthyEntity, BinarySensorEntity):
    entity_description: BMSBinaryDescription

    def __init__(
        self, coordinator, mac: str, description: BMSBinaryDescription
    ) -> None:
        self.entity_description = description
        super().__init__(coordinator, mac, description.key)

    @property
    def is_on(self) -> bool | None:
        value = self.battery.get(self.entity_description.section, {}).get(
            self.entity_description.key
        )
        return bool(value) if value is not None else None


class EcoWorthyConnectivitySensor(EcoWorthyEntity, BinarySensorEntity):
    _attr_translation_key = "connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, mac: str) -> None:
        super().__init__(coordinator, mac, "connectivity")

    @property
    def available(self) -> bool:
        return (
            self.coordinator.last_update_success
            and self.mac in self.coordinator.data["batteries"]
        )

    @property
    def is_on(self) -> bool:
        return bool(self.battery.get("available"))
