import time
from unittest import mock

import pytest
from django.core.cache import cache

from apps.accounts import otp
from apps.accounts.models import User

pytestmark = pytest.mark.django_db

PHONE = "09121112233"


def request_code(api_client, phone=PHONE) -> str:
    with mock.patch.object(otp, "generate_code", return_value="12345"):
        response = api_client.post("/api/auth/otp/request/", {"phone": phone}, format="json")
    assert response.status_code == 200, response.json()
    assert response.json()["expires_in"] == 120
    return "12345"


def test_full_login_flow_creates_user(api_client):
    code = request_code(api_client)
    response = api_client.post("/api/auth/otp/verify/", {"phone": PHONE, "code": code}, format="json")
    assert response.status_code == 200
    body = response.json()
    assert body["is_new"] is True
    assert body["user"]["phone"] == PHONE
    assert User.objects.filter(phone=PHONE).exists()

    me = api_client.get("/api/me/", HTTP_AUTHORIZATION=f"Bearer {body['access']}")
    assert me.json()["phone"] == PHONE

    # second login: not new
    cache.clear()
    code = request_code(api_client)
    body = api_client.post("/api/auth/otp/verify/", {"phone": PHONE, "code": code}, format="json").json()
    assert body["is_new"] is False


def test_persian_digits_accepted(api_client):
    request_code(api_client, "۰۹۱۲۱۱۱۲۲۳۳")
    response = api_client.post("/api/auth/otp/verify/", {"phone": PHONE, "code": "۱۲۳۴۵"}, format="json")
    assert response.status_code == 200


def test_wrong_code(api_client):
    request_code(api_client)
    response = api_client.post("/api/auth/otp/verify/", {"phone": PHONE, "code": "00000"}, format="json")
    assert response.status_code == 400
    assert response.json()["code"] == "otp_invalid"


def test_max_attempts(api_client, settings):
    settings.OTP_MAX_ATTEMPTS = 3
    request_code(api_client)
    codes = []
    for _ in range(3):
        codes.append(
            api_client.post("/api/auth/otp/verify/", {"phone": PHONE, "code": "00000"}, format="json").json()["code"]
        )
    assert codes == ["otp_invalid", "otp_invalid", "otp_max_attempts"]
    # even the right code no longer works
    response = api_client.post("/api/auth/otp/verify/", {"phone": PHONE, "code": "12345"}, format="json")
    assert response.json()["code"] == "otp_expired"


def test_expired_code(api_client):
    request_code(api_client)
    with mock.patch("apps.accounts.otp.time.time", return_value=time.time() + 121):
        response = api_client.post("/api/auth/otp/verify/", {"phone": PHONE, "code": "12345"}, format="json")
    assert response.json()["code"] == "otp_expired"


def test_resend_cooldown(api_client):
    request_code(api_client)
    response = api_client.post("/api/auth/otp/request/", {"phone": PHONE}, format="json")
    assert response.status_code == 429
    assert response.json()["code"] == "throttled"


def test_hourly_phone_limit(api_client, settings):
    settings.OTP_MAX_PER_HOUR_PHONE = 2
    settings.OTP_RESEND_SECONDS = 0
    for _ in range(2):
        cache.delete(f"otp:cooldown:{PHONE}")
        assert api_client.post("/api/auth/otp/request/", {"phone": PHONE}, format="json").status_code == 200
    cache.delete(f"otp:cooldown:{PHONE}")
    assert api_client.post("/api/auth/otp/request/", {"phone": PHONE}, format="json").status_code == 429


def test_refresh_rotation_and_logout(api_client):
    request_code(api_client)
    tokens = api_client.post("/api/auth/otp/verify/", {"phone": PHONE, "code": "12345"}, format="json").json()
    refreshed = api_client.post("/api/auth/token/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert refreshed.status_code == 200
    new = refreshed.json()
    assert new["refresh"] != tokens["refresh"]
    # old refresh is blacklisted
    again = api_client.post("/api/auth/token/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert again.status_code == 401
    assert again.json()["code"] == "not_authenticated"
    logout = api_client.post(
        "/api/auth/logout/", {"refresh": new["refresh"]}, format="json", HTTP_AUTHORIZATION=f"Bearer {new['access']}"
    )
    assert logout.status_code == 204
    assert api_client.post("/api/auth/token/refresh/", {"refresh": new["refresh"]}, format="json").status_code == 401


def test_update_profile(auth_client):
    response = auth_client.patch("/api/me/", {"first_name": "رضا", "phone": "09999999999"}, format="json")
    assert response.status_code == 200
    assert response.json()["first_name"] == "رضا"
    assert response.json()["phone"] == "09120000001"  # phone is read-only


ADDRESS = {
    "title": "محل کار",
    "receiver_name": "رضا",
    "receiver_phone": "09121234567",
    "province": "تهران",
    "city": "تهران",
    "postal_code": "۱۲۳۴۵۶۷۸۹۰",
    "address_line": "خیابان آزادی",
}


def test_address_crud_and_default(auth_client):
    first = auth_client.post("/api/me/addresses/", ADDRESS, format="json")
    assert first.status_code == 201
    assert first.json()["is_default"] is True
    assert first.json()["postal_code"] == "1234567890"
    second = auth_client.post("/api/me/addresses/", {**ADDRESS, "is_default": True}, format="json").json()
    listing = auth_client.get("/api/me/addresses/").json()
    assert [a["id"] for a in listing if a["is_default"]] == [second["id"]]
    patched = auth_client.patch(f"/api/me/addresses/{first.json()['id']}/", {"city": "کرج"}, format="json")
    assert patched.json()["city"] == "کرج"
    assert auth_client.delete(f"/api/me/addresses/{second['id']}/").status_code == 204
    remaining = auth_client.get("/api/me/addresses/").json()
    assert remaining[0]["is_default"] is True


def test_addresses_are_owner_only(auth_client, api_client):
    from .factories import AddressFactory

    other = AddressFactory(user__phone="09129999999")
    assert auth_client.get(f"/api/me/addresses/{other.id}/").status_code == 404
    assert auth_client.delete(f"/api/me/addresses/{other.id}/").status_code == 404
