"""EcoWorthy BMS Gateway integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GatewayClient
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_USE_SSL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS,
)
from .coordinator import EcoWorthyCoordinator

EcoWorthyConfigEntry = ConfigEntry[EcoWorthyCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: EcoWorthyConfigEntry) -> bool:
    """Set up a gateway from a UI config entry."""
    client = GatewayClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
        entry.data.get(CONF_USE_SSL, False),
        entry.data.get(CONF_TOKEN, ""),
    )
    interval = int(
        entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
    )
    coordinator = EcoWorthyCoordinator(hass, entry, client, timedelta(seconds=interval))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EcoWorthyConfigEntry) -> bool:
    """Unload a gateway config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_entry(hass: HomeAssistant, entry: EcoWorthyConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
