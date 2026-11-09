import pytest

from apps.core.pricing import calc_final_price
from apps.core.utils import gregorian_to_jalali, normalize_phone


@pytest.mark.parametrize(
    ("base", "discount", "expected"),
    [
        (1_000_000, 0, 1_000_000),
        (1_000_000, 20, 800_000),
        (1_234_567, 10, 1_111_000),  # 1,111,110 rounded down to 1,000
        (999, 50, 0),
        (4_890_000, 15, 4_156_000),
    ],
)
def test_calc_final_price(base, discount, expected):
    assert calc_final_price(base, discount) == expected


@pytest.mark.parametrize(
    "raw", ["09121234567", "۰۹۱۲۱۲۳۴۵۶۷", "+989121234567", "00989121234567", "9121234567", "0912 123 4567"]
)
def test_normalize_phone(raw):
    assert normalize_phone(raw) == "09121234567"


def test_gregorian_to_jalali():
    assert gregorian_to_jalali(2026, 3, 21) == (1405, 1, 1)
    assert gregorian_to_jalali(2026, 10, 30) == (1405, 8, 8)


@pytest.mark.django_db
def test_error_format_404(api_client):
    response = api_client.get("/api/products/does-not-exist/")
    assert response.status_code == 404
    assert response.json() == {"detail": "یافت نشد.", "code": "not_found", "errors": {}}


@pytest.mark.django_db
def test_error_format_401(api_client):
    response = api_client.get("/api/me/")
    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "not_authenticated"
    assert set(body) == {"detail", "code", "errors"}


@pytest.mark.django_db
def test_error_format_validation(api_client):
    response = api_client.post("/api/auth/otp/request/", {"phone": "123"}, format="json")
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert "phone" in body["errors"]


@pytest.mark.django_db
def test_health(api_client):
    response = api_client.get("/api/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.django_db
def test_schema_and_docs(api_client):
    assert api_client.get("/api/schema/").status_code == 200
    assert api_client.get("/api/docs/").status_code == 200
