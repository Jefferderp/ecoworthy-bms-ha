"""Data coordinator for EcoWorthy BMS Gateway."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GatewayAuthError, GatewayClient, GatewayConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class EcoWorthyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch one status document for every battery and entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: GatewayClient,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=update_interval,
            always_update=False,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_get_status()
        except GatewayAuthError as exc:
            raise ConfigEntryAuthFailed("Gateway authentication failed") from exc
        except GatewayConnectionError as exc:
            raise UpdateFailed(f"Error communicating with gateway: {exc}") from exc
