"""Sensors for EcoWorthy BMS Gateway."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.entity import EntityCategory

from . import EcoWorthyConfigEntry
from .entity import EcoWorthyEntity


@dataclass(frozen=True, kw_only=True)
class BMSSensorDescription(SensorEntityDescription):
    section: str = "telemetry"
    value_fn: Callable[[Any], Any] | None = None


SENSORS: tuple[BMSSensorDescription, ...] = (
    BMSSensorDescription(
        key="state_of_charge_pct",
        translation_key="state_of_charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BMSSensorDescription(
        key="pack_voltage_v",
        translation_key="pack_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    BMSSensorDescription(
        key="pack_current_a",
        translation_key="pack_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    BMSSensorDescription(
        key="pack_power_w",
        translation_key="pack_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    BMSSensorDescription(
        key="temperature_c",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    BMSSensorDescription(
        key="remaining_capacity_ah",
        translation_key="remaining_capacity",
        native_unit_of_measurement="Ah",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    BMSSensorDescription(
        key="design_capacity_ah",
        translation_key="design_capacity",
        native_unit_of_measurement="Ah",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    BMSSensorDescription(
        key="state_of_health_pct",
        translation_key="state_of_health",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BMSSensorDescription(
        key="direction",
        translation_key="direction",
        device_class=SensorDeviceClass.ENUM,
        options=["charging", "discharging", "idle"],
    ),
    BMSSensorDescription(
        key="eta_to_empty_seconds",
        translation_key="eta_to_empty",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        entity_registry_enabled_default=False,
    ),
    BMSSensorDescription(
        key="eta_to_full_seconds",
        translation_key="eta_to_full",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        entity_registry_enabled_default=False,
    ),
    BMSSensorDescription(
        key="cycles",
        translation_key="cycles",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BMSSensorDescription(
        key="cell_min_voltage",
        translation_key="cell_min_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BMSSensorDescription(
        key="cell_max_voltage",
        translation_key="cell_max_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BMSSensorDescription(
        key="cell_delta_voltage",
        translation_key="cell_delta_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BMSSensorDescription(
        key="rssi_dbm",
        translation_key="signal_strength",
        section="quality",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BMSSensorDescription(
        key="sample_age_seconds",
        translation_key="sample_age",
        section="quality",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BMSSensorDescription(
        key="consecutive_failures",
        translation_key="consecutive_failures",
        section="quality",
        state_class=SensorStateClass.MEASUREMENT,
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
            telemetry = battery.get("telemetry", {})
            quality = battery.get("quality", {})
            for description in SENSORS:
                identity = (mac, description.key)
                section = quality if description.section == "quality" else telemetry
                if description.key in section and identity not in known:
                    known.add(identity)
                    entities.append(EcoWorthySensor(coordinator, mac, description))
            for index, _value in enumerate(telemetry.get("cell_voltages", []), start=1):
                identity = (mac, f"cell_{index}_voltage")
                if identity not in known:
                    known.add(identity)
                    entities.append(EcoWorthyCellSensor(coordinator, mac, index))
            for index, _value in enumerate(telemetry.get("temp_values", []), start=1):
                identity = (mac, f"temperature_{index}")
                if identity not in known:
                    known.add(identity)
                    entities.append(EcoWorthyTemperatureSensor(coordinator, mac, index))
        if entities:
            async_add_entities(entities)

    discover_entities()
    entry.async_on_unload(coordinator.async_add_listener(discover_entities))


class EcoWorthySensor(EcoWorthyEntity, SensorEntity):
    entity_description: BMSSensorDescription

    def __init__(
        self, coordinator, mac: str, description: BMSSensorDescription
    ) -> None:
        self.entity_description = description
        super().__init__(coordinator, mac, description.key)

    @property
    def native_value(self):
        value = self.battery.get(self.entity_description.section, {}).get(
            self.entity_description.key
        )
        return (
            self.entity_description.value_fn(value)
            if self.entity_description.value_fn
            else value
        )


class EcoWorthyCellSensor(EcoWorthyEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, mac: str, index: int) -> None:
        self.index = index
        self._attr_translation_key = "cell_voltage"
        self._attr_translation_placeholders = {"number": str(index)}
        super().__init__(coordinator, mac, f"cell_{index}_voltage")

    @property
    def native_value(self):
        values = self.battery.get("telemetry", {}).get("cell_voltages", [])
        return values[self.index - 1] if len(values) >= self.index else None


class EcoWorthyTemperatureSensor(EcoWorthyEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, mac: str, index: int) -> None:
        self.index = index
        self._attr_translation_key = "temperature_probe"
        self._attr_translation_placeholders = {"number": str(index)}
        super().__init__(coordinator, mac, f"temperature_{index}")

    @property
    def native_value(self):
        values = self.battery.get("telemetry", {}).get("temp_values", [])
        if len(values) < self.index:
            return None
        value = values[self.index - 1]
        return value.get("value") if isinstance(value, dict) else value
