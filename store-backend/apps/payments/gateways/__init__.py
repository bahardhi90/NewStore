from ..models import PaymentMethod
from .base import GatewayError, PaymentGateway, StartResult, VerifyResult
from .digipay import DigipayGateway
from .fake import FakeGateway
from .snapppay import SnappPayGateway
from .zarinpal import ZarinpalGateway

GATEWAYS: dict[str, type[PaymentGateway]] = {
    DigipayGateway.name: DigipayGateway,
    FakeGateway.name: FakeGateway,
    SnappPayGateway.name: SnappPayGateway,
    ZarinpalGateway.name: ZarinpalGateway,
}


def get_gateway(name: str) -> PaymentGateway:
    """Works for disabled methods too, so payments already in progress can still be verified."""
    try:
        gateway_class = GATEWAYS[name]
    except KeyError as exc:
        raise RuntimeError(f"Unknown payment gateway: {name}") from exc
    return gateway_class(PaymentMethod.objects.filter(code=name).first() or PaymentMethod(code=name))


__all__ = ["GatewayError", "PaymentGateway", "StartResult", "VerifyResult", "get_gateway"]
