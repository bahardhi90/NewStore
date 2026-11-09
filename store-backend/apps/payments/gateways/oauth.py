"""Shared HTTP + cached OAuth token handling for the installment gateways."""

import logging
from abc import abstractmethod

import httpx
from django.core.cache import cache

from ..models import token_cache_key
from .base import GatewayError, PaymentGateway

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_MARGIN_SECONDS = 60


class OAuthGateway(PaymentGateway):
    timeout = httpx.Timeout(45.0, connect=20.0)

    @property
    @abstractmethod
    def api_base(self) -> str:
        """Base URL without a trailing slash."""

    @abstractmethod
    def _request_token(self) -> httpx.Response:
        """Ask the gateway for an access token."""

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json"}

    def _token(self) -> str:
        key = token_cache_key(self.name)
        token = cache.get(key)
        if token:
            return token
        try:
            response = self._request_token()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise GatewayError(f"{self.name} token request failed: {exc}") from exc
        token = body.get("access_token")
        if not token:
            raise GatewayError(f"{self.name} rejected the credentials ({response.status_code})")
        ttl = int(body.get("expires_in") or 3600) - TOKEN_EXPIRY_MARGIN_SECONDS
        cache.set(key, token, max(ttl, 1))
        return token

    def _call(self, method: str, path: str, *, params: dict | None = None, json: dict | None = None) -> dict:
        response = self._send(method, path, params, json)
        if response.status_code == 401:  # token revoked or expired early
            cache.delete(token_cache_key(self.name))
            response = self._send(method, path, params, json)
        if response.status_code >= 500:
            raise GatewayError(f"{self.name} server error ({response.status_code})")
        try:
            return response.json()
        except ValueError as exc:
            raise GatewayError(f"Invalid JSON from {self.name} ({response.status_code})") from exc

    def _send(self, method: str, path: str, params: dict | None, json: dict | None) -> httpx.Response:
        headers = {**self._headers(), "Authorization": f"Bearer {self._token()}"}
        try:
            return httpx.request(
                method, f"{self.api_base}{path}", params=params, json=json, headers=headers, timeout=self.timeout
            )
        except httpx.HTTPError as exc:
            raise GatewayError(str(exc)) from exc
