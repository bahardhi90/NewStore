import pytest

from .factories import VariantFactory

pytestmark = pytest.mark.django_db


def test_cart_requires_auth(api_client):
    assert api_client.get("/api/cart/").status_code == 401


def test_add_update_remove(auth_client, variant):
    response = auth_client.post("/api/cart/items/", {"variant_id": variant.id, "quantity": 2}, format="json")
    assert response.status_code == 201
    cart = response.json()
    assert cart["item_count"] == 2
    assert cart["subtotal"] == 4_000_000
    assert cart["discount_total"] == 800_000
    assert cart["total"] == 3_200_000
    item_id = cart["items"][0]["id"]
    assert cart["items"][0]["line_total"] == 3_200_000

    cart = auth_client.patch(f"/api/cart/items/{item_id}/", {"quantity": 3}, format="json").json()
    assert cart["item_count"] == 3
    cart = auth_client.delete(f"/api/cart/items/{item_id}/").json()
    assert cart["items"] == []
    assert cart["total"] == 0


def test_adding_same_variant_sums(auth_client, variant):
    auth_client.post("/api/cart/items/", {"variant_id": variant.id, "quantity": 2}, format="json")
    cart = auth_client.post("/api/cart/items/", {"variant_id": variant.id, "quantity": 1}, format="json").json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 3


def test_out_of_stock(auth_client, variant):
    response = auth_client.post("/api/cart/items/", {"variant_id": variant.id, "quantity": 6}, format="json")
    assert response.status_code == 409
    assert response.json()["code"] == "out_of_stock"
    assert "variant_id" in response.json()["errors"]


def test_quantity_limit(auth_client, settings):
    v = VariantFactory(stock=50)
    response = auth_client.post("/api/cart/items/", {"variant_id": v.id, "quantity": 11}, format="json")
    assert response.status_code == 400


def test_inactive_product(auth_client):
    v = VariantFactory(product__is_active=False)
    response = auth_client.post("/api/cart/items/", {"variant_id": v.id, "quantity": 1}, format="json")
    assert response.status_code == 404


def test_cannot_touch_other_users_items(auth_client, variant):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    from .factories import UserFactory

    other = APIClient()
    other.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(UserFactory()).access_token}")
    item_id = other.post("/api/cart/items/", {"variant_id": variant.id, "quantity": 1}, format="json").json()["items"][
        0
    ]["id"]
    assert auth_client.delete(f"/api/cart/items/{item_id}/").status_code == 404


def test_merge(auth_client):
    plenty = VariantFactory(stock=10)
    few = VariantFactory(stock=2)
    sold_out = VariantFactory(stock=0)
    auth_client.post("/api/cart/items/", {"variant_id": plenty.id, "quantity": 1}, format="json")
    cart = auth_client.post(
        "/api/cart/merge/",
        {
            "items": [
                {"variant_id": plenty.id, "quantity": 2},
                {"variant_id": few.id, "quantity": 5},
                {"variant_id": sold_out.id, "quantity": 1},
                {"variant_id": 999999, "quantity": 1},
            ]
        },
        format="json",
    ).json()
    quantities = {i["variant"]["id"]: i["quantity"] for i in cart["items"]}
    assert quantities == {plenty.id: 3, few.id: 2}
    assert len(cart["warnings"]) == 3


def test_item_warning_when_stock_drops(auth_client, variant):
    auth_client.post("/api/cart/items/", {"variant_id": variant.id, "quantity": 4}, format="json")
    variant.stock = 1
    variant.save()
    cart = auth_client.get("/api/cart/").json()
    assert cart["items"][0]["warning"]
