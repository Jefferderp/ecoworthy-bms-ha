"""Diagnostics for EcoWorthy BMS Gateway."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data

from . import EcoWorthyConfigEntry
from .const import CONF_TOKEN

TO_REDACT = {CONF_TOKEN}


async def async_get_config_entry_diagnostics(hass, entry: EcoWorthyConfigEntry):
    """Return config and the latest gateway document without credentials."""
    return {
        "config_entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "data": entry.runtime_data.data,
    }
