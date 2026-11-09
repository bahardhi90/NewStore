"""Digipay UPG (wallet + installment). Amounts are sent in Rial (Toman * 10).

Docs: https://www.mydigipay.com/developers/docs/upg/
"""

import logging
import secrets

import httpx
from django.utils import timezone

from apps.content.models import SiteSettings
from apps.core.pricing import toman_to_rial

from .base import GatewayError, StartResult, VerifyResult
from .oauth import OAuthGateway

logger = logging.getLogger(__name__)

LIVE_URL = "https://api.mydigipay.com/digipay/api"
SANDBOX_URL = "https://uat.mydigipay.info/digipay/api"
API_VERSION = "2022-02-02"
TICKET_TYPE = 11  # the docs use 11 for every UPG ticket; the customer picks the method on Digipay's page
CREDIT_TYPES = {"5", "13"}  # CREDIT and BNPL purchases must also be reported as delivered
PRODUCT_TYPE_DURABLE_CONSUMABLE = 4


class DigipayGateway(OAuthGateway):
    name = "digipay"

    @property
    def api_base(self) -> str:
        url = self.config.api_url or (SANDBOX_URL if self.config.sandbox else LIVE_URL)
        return url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {**super()._headers(), "Agent": "WEB", "Digipay-Version": API_VERSION}

    def _request_token(self) -> httpx.Response:
        form = {"username": self.config.username, "password": self.config.password, "grant_type": "password"}
        return httpx.post(
            f"{self.api_base}/oauth/token",
            files={key: (None, value) for key, value in form.items()},  # the API expects form-data
            auth=(self.config.client_id, self.config.client_secret),
            timeout=self.timeout,
        )

    def _basket(self, order, order_number: str) -> dict:
        brand = SiteSettings.load().brand_name
        items = [
            {
                "sellerId": self.config.username,
                "supplierId": self.config.username,
                "productCode": item.sku or str(item.variant_id),
                "brand": brand,
                "productType": PRODUCT_TYPE_DURABLE_CONSUMABLE,
                "count": item.quantity,
                "categoryId": self.config.category,
            }
            for item in order.items.all()
        ]
        return {"basketId": order_number, "items": items}

    def start(self, *, amount_toman, description, callback_url, mobile, order_number, order=None) -> StartResult:
        authority = f"DP{secrets.token_hex(12).upper()}"
        body = self._call(
            "POST",
            "/tickets/business",
            params={"type": TICKET_TYPE},
            json={
                "amount": toman_to_rial(amount_toman),
                "cellNumber": mobile,
                "providerId": authority,
                "callbackUrl": self.post_callback_url(authority),
                "basketDetailsDto": self._basket(order, order_number),
            },
        )
        redirect_url = body.get("redirectUrl")
        if (body.get("result") or {}).get("status") != 0 or not redirect_url:
            logger.warning("Digipay ticket failed: %s", body)
            raise GatewayError(f"Digipay ticket failed: {body.get('result')}")
        return StartResult(authority=authority, redirect_url=redirect_url, raw=body)

    def verify(self, *, authority, amount_toman, context=None) -> VerifyResult:
        context = context or {}
        tracking_code = context.get("tracking_code")
        purchase_type = str(context.get("purchase_type") or "")
        if not tracking_code or not purchase_type:
            return VerifyResult(success=False, raw={"error": "missing_callback_data"})

        body = self._call(
            "POST",
            "/purchases/verify",
            params={"type": purchase_type},
            json={"trackingCode": tracking_code, "providerId": authority},
        )
        if (body.get("result") or {}).get("status") != 0:
            return VerifyResult(success=False, raw=body)
        if body.get("providerId") != authority or body.get("amount") != toman_to_rial(amount_toman):
            logger.error("Digipay verify mismatch for %s: %s", authority, body)
            return VerifyResult(success=False, raw=body)

        raw = dict(body)
        if purchase_type in CREDIT_TYPES:
            self._deliver(tracking_code, purchase_type, context.get("order"), raw)
        return VerifyResult(
            success=True, ref_id=str(body.get("rrn") or tracking_code), card_pan=body.get("maskedPan") or "", raw=raw
        )

    def _deliver(self, tracking_code: str, purchase_type: str, order, raw: dict) -> None:
        """The customer has paid at this point, so a delivery failure is recorded instead of failing the payment."""
        try:
            raw["deliver"] = self._call(
                "POST",
                "/purchases/deliver",
                params={"type": purchase_type},
                json={
                    "deliveryDate": int(timezone.now().timestamp() * 1000),
                    "invoiceNumber": order.number,
                    "trackingCode": tracking_code,
                    "products": [item.sku or str(item.variant_id) for item in order.items.all()],
                },
            )
        except GatewayError as exc:
            logger.error("Digipay deliver failed for order %s: %s", order.number, exc)
            raw["deliver"] = {"error": str(exc)}
