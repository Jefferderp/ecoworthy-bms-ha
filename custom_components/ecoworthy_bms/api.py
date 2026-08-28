"""Async client for an EcoWorthy BMS Gateway."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientSession


class GatewayError(Exception):
    """Base gateway error."""


class GatewayConnectionError(GatewayError):
    """The gateway could not be reached or returned invalid data."""


class GatewayAuthError(GatewayError):
    """The gateway rejected authentication."""


@dataclass(slots=True)
class GatewayClient:
    """Small Home Assistant-independent HTTP API client."""

    session: ClientSession
    host: str
    port: int
    use_ssl: bool = False
    token: str = ""
    timeout: float = 10

    @property
    def base_url(self) -> str:
        scheme = "https" if self.use_ssl else "http"
        host = self.host.strip().rstrip("/")
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        return f"{scheme}://{host}:{self.port}"

    async def async_get_status(self) -> dict[str, Any]:
        """Fetch and minimally validate the versioned status document."""
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            async with asyncio.timeout(self.timeout):
                response = await self.session.get(
                    f"{self.base_url}/api/v1/status", headers=headers
                )
                if response.status in (401, 403):
                    await response.read()
                    raise GatewayAuthError("invalid bearer token")
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except GatewayAuthError:
            raise
        except (TimeoutError, ClientError, ValueError) as exc:
            raise GatewayConnectionError(str(exc)) from exc
        if not isinstance(payload, dict):
            raise GatewayConnectionError("response is not an object")
        if not isinstance(payload.get("server_id"), str) or not payload["server_id"]:
            raise GatewayConnectionError("response has no server_id")
        if not isinstance(payload.get("batteries"), dict):
            raise GatewayConnectionError("response has no batteries object")
        version = payload.get("api_schema_version")
        if not isinstance(version, str) or version.split(".", 1)[0] != "1":
            raise GatewayConnectionError(f"unsupported API schema: {version!r}")
        return payload
