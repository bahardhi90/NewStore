"""Development gateway: no real money. Redirects straight back to the callback with Status=OK."""

import secrets
from urllib.parse import urlencode

from .base import PaymentGateway, StartResult, VerifyResult


class FakeGateway(PaymentGateway):
    name = "fake"

    def start(self, *, amount_toman, description, callback_url, mobile, order_number, order=None) -> StartResult:
        authority = f"FAKE{secrets.token_hex(16).upper()}"
        query = urlencode({"Authority": authority, "Status": "OK"})
        return StartResult(authority=authority, redirect_url=f"{callback_url}?{query}", raw={"fake": True})

    def verify(self, *, authority, amount_toman, context=None) -> VerifyResult:
        ref_id = str(secrets.randbelow(10**10)).zfill(10)
        return VerifyResult(success=True, ref_id=ref_id, card_pan="6037****1234", raw={"fake": True, "ref_id": ref_id})
