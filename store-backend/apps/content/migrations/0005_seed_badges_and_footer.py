from django.db import migrations

BADGES = [
    ("return", "۷ روز ضمانت بازگشت", "بدون پرسش، کامل"),
    ("truck", "ارسال سریع", "به سراسر ایران"),
    ("shield", "پرداخت امن", "درگاه معتبر بانکی"),
    ("badge", "ضمانت اصالت", "تولید و دوخت باکیفیت"),
]

COLUMNS = [
    ("راهنمای خرید", [("سوالات متداول", "/faq"), ("شرایط مرجوعی", "/returns"), ("پیگیری سفارش", "/account/orders")]),
    ("فروشگاه", [("درباره ما", "/about"), ("تماس با ما", "/contact"), ("شعب", "/stores")]),
]


def seed(apps, schema_editor):
    """Moves the texts that were written in the frontend code into admin, unchanged."""
    SiteSettings = apps.get_model("content", "SiteSettings")
    TrustBadge = apps.get_model("content", "TrustBadge")
    FooterColumn = apps.get_model("content", "FooterColumn")
    FooterLink = apps.get_model("content", "FooterLink")

    site, _ = SiteSettings.objects.get_or_create(pk=1)
    if not site.instagram_url and not site.telegram_url:
        site.instagram_url, site.telegram_url = "https://instagram.com", "https://t.me"
        site.save(update_fields=["instagram_url", "telegram_url"])
    if not TrustBadge.objects.exists():
        for order, (icon, title, subtitle) in enumerate(BADGES):
            TrustBadge.objects.create(site=site, icon=icon, title=title, subtitle=subtitle, order=order)
    if not FooterColumn.objects.exists():
        for order, (title, links) in enumerate(COLUMNS):
            column = FooterColumn.objects.create(site=site, title=title, order=order)
            for link_order, (link_title, url) in enumerate(links):
                FooterLink.objects.create(column=column, title=link_title, url=url, order=link_order)


class Migration(migrations.Migration):
    dependencies = [("content", "0004_site_content_and_banner_video")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
