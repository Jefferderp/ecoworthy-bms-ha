"""UI configuration for EcoWorthy BMS Gateway."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GatewayAuthError, GatewayClient, GatewayConnectionError
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_USE_SSL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_HOST, default=defaults.get(CONF_HOST, "")
            ): str,
            vol.Required(
                CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Required(CONF_USE_SSL, default=defaults.get(CONF_USE_SSL, False)): bool,
            vol.Optional(
                CONF_TOKEN, default=defaults.get(CONF_TOKEN, "")
            ): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=3600)),
        }
    )


async def _validate(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    client = GatewayClient(
        async_get_clientsession(hass),
        data[CONF_HOST].strip(),
        data[CONF_PORT],
        data[CONF_USE_SSL],
        data.get(CONF_TOKEN, ""),
    )
    return await client.async_get_status()


class EcoWorthyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a gateway entirely through the Home Assistant UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_HOST] = user_input[CONF_HOST].strip()
            try:
                status = await _validate(self.hass, user_input)
            except GatewayAuthError:
                errors["base"] = "invalid_auth"
            except GatewayConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - config flows must surface unknown failures
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(status["server_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=status.get("server_name") or user_input[CONF_HOST],
                    data=user_input,
                )
        return self.async_show_form(
            step_id="user", data_schema=_schema(user_input or {}), errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        defaults = {**entry.data, **entry.options}
        if user_input is not None:
            user_input[CONF_HOST] = user_input[CONF_HOST].strip()
            try:
                status = await _validate(self.hass, user_input)
            except GatewayAuthError:
                errors["base"] = "invalid_auth"
            except GatewayConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                if entry.unique_id and entry.unique_id != status["server_id"]:
                    errors["base"] = "wrong_gateway"
                else:
                    return self.async_update_reload_and_abort(
                        entry, data=user_input, unique_id=status["server_id"]
                    )
            defaults = user_input
        return self.async_show_form(
            step_id="reconfigure", data_schema=_schema(defaults), errors=errors
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        entry = self._reauth_entry
        errors: dict[str, str] = {}
        if user_input is not None:
            updated = {**entry.data, CONF_TOKEN: user_input.get(CONF_TOKEN, "")}
            try:
                await _validate(self.hass, updated)
            except GatewayAuthError:
                errors["base"] = "invalid_auth"
            except GatewayConnectionError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(entry, data=updated)
        schema = vol.Schema(
            {
                vol.Optional(CONF_TOKEN, default=""): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                )
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=schema, errors=errors
        )
