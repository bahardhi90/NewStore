"""Zarinpal REST API v4. Amounts are sent in Rial (Toman * 10)."""

import logging

import httpx
from django.conf import settings

from apps.core.pricing import toman_to_rial

from .base import GatewayError, PaymentGateway, StartResult, VerifyResult

logger = logging.getLogger(__name__)


class ZarinpalGateway(PaymentGateway):
    name = "zarinpal"
    timeout = httpx.Timeout(15.0, connect=5.0)

    def __init__(self, config) -> None:
        super().__init__(config)
        self.merchant_id = config.merchant_id or settings.ZARINPAL_MERCHANT_ID
        if not self.merchant_id:
            raise GatewayError("Zarinpal merchant id is not set")
        host = "sandbox.zarinpal.com" if config.sandbox else "payment.zarinpal.com"
        self.api_base = f"https://{host}/pg/v4/payment"
        self.start_pay_url = f"https://{host}/pg/StartPay/"

    def _post(self, endpoint: str, payload: dict) -> dict:
        try:
            response = httpx.post(
                f"{self.api_base}/{endpoint}.json",
                json=payload,
                headers={"Accept": "application/json"},
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise GatewayError(str(exc)) from exc
        try:
            return response.json()
        except ValueError as exc:
            raise GatewayError(f"Invalid JSON from Zarinpal ({response.status_code})") from exc

    def start(self, *, amount_toman, description, callback_url, mobile, order_number, order=None) -> StartResult:
        payload = {
            "merchant_id": self.merchant_id,
            "amount": toman_to_rial(amount_toman),
            "callback_url": callback_url,
            "description": description,
            "metadata": {"mobile": mobile, "order_id": order_number},
        }
        body = self._post("request", payload)
        data = body.get("data") or {}
        if data.get("code") != 100 or not data.get("authority"):
            logger.warning("Zarinpal request failed: %s", body)
            raise GatewayError(f"Zarinpal request failed: {body.get('errors')}")
        authority = data["authority"]
        return StartResult(authority=authority, redirect_url=f"{self.start_pay_url}{authority}", raw=body)

    def verify(self, *, authority, amount_toman, context=None) -> VerifyResult:
        body = self._post(
            "verify",
            {"merchant_id": self.merchant_id, "amount": toman_to_rial(amount_toman), "authority": authority},
        )
        data = body.get("data") or {}
        code = data.get("code")
        if code in (100, 101):  # 101 = already verified
            return VerifyResult(
                success=True, ref_id=str(data.get("ref_id", "")), card_pan=data.get("card_pan", ""), raw=body
            )
        if body.get("errors") and not data:
            # Business errors (e.g. -51 payment failed) are a normal "unsuccessful" result.
            return VerifyResult(success=False, raw=body)
        raise GatewayError(f"Unexpected Zarinpal verify response: {body}")
