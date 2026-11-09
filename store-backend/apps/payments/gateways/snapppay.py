"""SnappPay installment payments. Amounts are sent in Rial (Toman * 10).

Flow: token -> redirect -> verify -> settle. A payment that was verified but not settled does not
go through, so a repeated verify picks up from the state SnappPay reports.
"""

import logging
import secrets

import httpx

from apps.core.pricing import toman_to_rial

from .base import GatewayError, StartResult, VerifyResult
from .oauth import OAuthGateway

logger = logging.getLogger(__name__)

LIVE_URL = "https://api.snapppay.ir"
COMMISSION_TYPE = 100


def to_international(mobile: str) -> str:
    return f"+98{mobile[1:]}" if mobile.startswith("0") else mobile


class SnappPayGateway(OAuthGateway):
    name = "snapppay"

    @property
    def api_base(self) -> str:
        return (self.config.api_url or LIVE_URL).rstrip("/")

    def _request_token(self) -> httpx.Response:
        return httpx.post(
            f"{self.api_base}/api/online/v1/oauth/token",
            data={
                "grant_type": "password",
                "scope": "online-merchant",
                "username": self.config.username,
                "password": self.config.password,
            },
            auth=(self.config.client_id, self.config.client_secret),
            timeout=self.timeout,
        )

    def _cart(self, order) -> dict:
        items = [
            {
                "id": item.id,
                "name": item.title,
                "count": item.quantity,
                "amount": toman_to_rial(item.final_unit_price),
                "category": self.config.category,
                "commissionType": COMMISSION_TYPE,
            }
            for item in order.items.all()
        ]
        return {
            "cartId": order.id,
            "cartItems": items,
            "totalAmount": toman_to_rial(order.total),
            "shippingAmount": toman_to_rial(order.shipping_cost),
            "taxAmount": 0,
            "isShipmentIncluded": True,
            "isTaxIncluded": True,
        }

    def start(self, *, amount_toman, description, callback_url, mobile, order_number, order=None) -> StartResult:
        authority = f"SP{secrets.token_hex(12).upper()}"
        body = self._call(
            "POST",
            "/api/online/payment/v1/token",
            json={
                "amount": toman_to_rial(amount_toman),
                "discountAmount": 0,
                "mobile": to_international(mobile),
                "paymentMethodTypeDto": "INSTALLMENT",
                "returnURL": self.post_callback_url(authority),
                "transactionId": authority,
                "cartList": [self._cart(order)],
            },
        )
        data = body.get("response") or {}
        if not body.get("successful") or not data.get("paymentPageUrl") or not data.get("paymentToken"):
            logger.warning("SnappPay token failed: %s", body)
            raise GatewayError(f"SnappPay token failed: {body}")
        return StartResult(authority=authority, redirect_url=data["paymentPageUrl"], raw=body)

    def _status(self, token: str) -> str:
        body = self._call("GET", "/api/online/payment/v1/status", params={"paymentToken": token})
        return str((body.get("response") or {}).get("status") or "")

    def verify(self, *, authority, amount_toman, context=None) -> VerifyResult:
        start_response = (context or {}).get("start_response") or {}
        token = (start_response.get("response") or {}).get("paymentToken")
        if not token:
            return VerifyResult(success=False, raw={"error": "missing_payment_token"})

        verified = self._call("POST", "/api/online/payment/v1/verify", json={"paymentToken": token})
        status = "VERIFY" if verified.get("successful") else self._status(token)
        if status not in ("VERIFY", "SETTLE"):
            return VerifyResult(success=False, raw=verified)

        settled = {}
        if status == "VERIFY":
            settled = self._call("POST", "/api/online/payment/v1/settle", json={"paymentToken": token})
            if not settled.get("successful") and self._status(token) != "SETTLE":
                # Stays retryable: the next verify call sees status VERIFY and settles again.
                raise GatewayError(f"SnappPay settle failed: {settled}")
        return VerifyResult(success=True, ref_id=authority, raw={"verify": verified, "settle": settled})
