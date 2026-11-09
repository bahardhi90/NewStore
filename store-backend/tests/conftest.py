import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .factories import AddressFactory, ShippingMethodFactory, UserFactory, VariantFactory


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory(phone="09120000001")


@pytest.fixture
def auth_client(user) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


@pytest.fixture
def variant(db):
    return VariantFactory(stock=5, product__base_price=2_000_000, product__discount_percent=20)


@pytest.fixture
def address(user):
    return AddressFactory(user=user)


@pytest.fixture
def shipping(db):
    return ShippingMethodFactory(cost=60_000)
