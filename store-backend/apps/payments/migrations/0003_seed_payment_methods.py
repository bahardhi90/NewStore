from django.conf import settings
from django.db import migrations

METHODS = [
    ("zarinpal", "پرداخت اینترنتی", "پرداخت با تمام کارت‌های بانکی عضو شتاب", 1),
    ("digipay", "دیجی‌پی", "خرید اعتباری و اقساطی با دیجی‌پی", 2),
    ("snapppay", "اسنپ‌پی", "خرید اقساطی با اسنپ‌پی", 3),
    ("fake", "درگاه آزمایشی", "فقط برای محیط توسعه", 4),
]


def seed(apps, schema_editor):
    """Keeps what .env selected until now. Installment methods start off until the admin enables them."""
    PaymentMethod = apps.get_model("payments", "PaymentMethod")
    for code, title, description, order in METHODS:
        PaymentMethod.objects.get_or_create(
            code=code,
            defaults={
                "title": title,
                "description": description,
                "order": order,
                "is_active": code == settings.PAYMENT_GATEWAY,
                "sandbox": code == "zarinpal" and settings.ZARINPAL_SANDBOX,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("payments", "0002_paymentmethod")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
