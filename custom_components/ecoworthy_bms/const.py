"""Constants for the EcoWorthy BMS Gateway integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "ecoworthy_bms"
PLATFORMS = ["sensor", "binary_sensor"]
CONF_TOKEN = "token"
CONF_USE_SSL = "use_ssl"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_PORT = 8765
DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 5
DEFAULT_TIMEOUT = 10
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
