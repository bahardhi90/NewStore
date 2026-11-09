from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings

from ..models import PaymentMethod


class GatewayError(Exception):
    """Network error or unexpected response from the gateway."""


@dataclass
class StartResult:
    authority: str
    redirect_url: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerifyResult:
    success: bool
    ref_id: str = ""
    card_pan: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class PaymentGateway(ABC):
    name: str = ""

    def __init__(self, config: PaymentMethod) -> None:
        self.config = config

    def post_callback_url(self, authority: str) -> str:
        """For gateways that POST the browser back: a frontend route turns that into a normal redirect."""
        return f"{settings.PAYMENT_POST_CALLBACK_URL}?authority={authority}"

    @abstractmethod
    def start(
        self, *, amount_toman: int, description: str, callback_url: str, mobile: str, order_number: str, order=None
    ) -> StartResult:
        """Create a payment and return where to redirect the user."""

    @abstractmethod
    def verify(self, *, authority: str, amount_toman: int, context: dict | None = None) -> VerifyResult:
        """Server-to-server verification after the user comes back.

        `context` holds what some gateways need besides the authority: order, start_response,
        tracking_code and purchase_type.
        """
