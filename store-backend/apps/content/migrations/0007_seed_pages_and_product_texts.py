from django.db import migrations

SHIPPING = """ارسال به سراسر کشور با پست پیشتاز و تیپاکس؛ ارسال رایگان برای خریدهای بالای ۳ میلیون تومان.
تا ۷ روز پس از تحویل می‌توانید کالا را بدون استفاده و با برچسب سالم مرجوع کنید.
تعویض سایز رایگان است."""

SIZE_NOTE = "اندازه‌ها به سانتی‌متر است. اگر بین دو سایز هستید، سایز بزرگ‌تر را انتخاب کنید."

SIZE_CHARTS = [
    (
        "کاپشن، کت و پیراهن",
        "سایز، دور سینه، قد، سرشانه تا سرآستین",
        "S، ۹۶–۱۰۰، ۷۰، ۶۲\nM، ۱۰۰–۱۰۴، ۷۲، ۶۳\nL، ۱۰۴–۱۱۰، ۷۴، ۶۴\nXL، ۱۱۰–۱۱۶، ۷۶، ۶۵\nXXL، ۱۱۶–۱۲۲، ۷۸، ۶۶",
    ),
    ("شلوار", "سایز، دور کمر، قد", "۳۰، ۷۶، ۱۰۲\n۳۲، ۸۱، ۱۰۳\n۳۴، ۸۶، ۱۰۴\n۳۶، ۹۱، ۱۰۵\n۳۸، ۹۶، ۱۰۶"),
]

PAGES = {
    "about": (
        "درباره ما",
        "ما فعالیت خود را با یک هدف ساده آغاز کردیم: پوشاک مردانه باکیفیت، با دوخت دقیق و قیمت منصفانه.\n\n"
        "همه محصولات ما با پارچه‌های منتخب و در کارگاه‌های داخلی تولید می‌شوند و پیش از ارسال، کنترل کیفیت می‌شوند.\n\n"
        "در شعب حضوری و فروشگاه اینترنتی، تیم ما آماده است تا در انتخاب سایز و استایل مناسب کنارتان باشد.",
        [],
    ),
    "contact": (
        "تماس با ما",
        "برای پیگیری سفارش، مشاوره خرید یا ثبت شکایت با ما در تماس باشید.",
        [
            ("تلفن پشتیبانی", "021-22000000"),
            ("ایمیل", "support@example.com"),
            ("ساعات پاسخگویی", "شنبه تا پنجشنبه، ۹ تا ۱۸"),
            ("آدرس دفتر مرکزی", "تهران، خیابان ولیعصر، مجتمع تجاری نگین، طبقه اول"),
        ],
    ),
    "faq": (
        "سوالات متداول",
        "",
        [
            (
                "سفارش من چه زمانی به دستم می‌رسد؟",
                "سفارش‌ها حداکثر یک روز کاری پس از پرداخت ارسال می‌شوند. زمان تحویل با پست پیشتاز ۳ تا ۵ روز و با تیپاکس ۱ تا ۳ روز کاری است.",
            ),
            (
                "هزینه ارسال چقدر است؟",
                "هزینه ارسال بر اساس روش انتخابی در مرحله پرداخت نمایش داده می‌شود. برای خریدهای بالای ۳ میلیون تومان ارسال با پست رایگان است.",
            ),
            (
                "چطور سایز مناسب را انتخاب کنم؟",
                "در صفحه هر محصول، دکمه «راهنمای سایز» جدول اندازه‌ها را نمایش می‌دهد. اگر بین دو سایز هستید، سایز بزرگ‌تر را انتخاب کنید.",
            ),
            (
                "آیا امکان تعویض یا مرجوع کردن کالا وجود دارد؟",
                "بله. تا ۷ روز پس از تحویل، کالای استفاده‌نشده با برچسب سالم قابل مرجوع یا تعویض است. جزئیات در صفحه شرایط مرجوعی آمده است.",
            ),
            (
                "پرداخت امن است؟",
                "پرداخت از طریق درگاه معتبر بانکی انجام می‌شود و اطلاعات کارت شما هرگز در سایت ما ذخیره نمی‌شود.",
            ),
            (
                "اگر پرداخت ناموفق بود و پول کسر شد چه کنم؟",
                "در صورت ناموفق بودن تراکنش، مبلغ کسرشده حداکثر ظرف ۷۲ ساعت توسط بانک به حساب شما بازمی‌گردد.",
            ),
        ],
    ),
    "returns": (
        "شرایط مرجوعی و تعویض",
        "",
        [
            ("مهلت مرجوعی", "تا ۷ روز پس از تحویل سفارش می‌توانید درخواست مرجوعی یا تعویض ثبت کنید."),
            ("شرایط کالا", "کالا باید استفاده‌نشده، شسته‌نشده و همراه با برچسب و بسته‌بندی اصلی باشد."),
            (
                "هزینه‌ها",
                "تعویض سایز رایگان است. در صورت مرجوعی به دلیل انصراف از خرید، هزینه ارسال برگشت بر عهده مشتری است.",
            ),
            ("بازگشت وجه", "پس از دریافت و بررسی کالا، مبلغ حداکثر ظرف ۷ روز کاری به حساب شما واریز می‌شود."),
        ],
    ),
}


def seed(apps, schema_editor):
    """Moves the texts that were written in the frontend code into admin, unchanged."""
    SiteSettings = apps.get_model("content", "SiteSettings")
    SizeChart = apps.get_model("content", "SizeChart")
    Page = apps.get_model("content", "Page")
    PageItem = apps.get_model("content", "PageItem")

    site, _ = SiteSettings.objects.get_or_create(pk=1)
    if not site.product_shipping_text:
        site.product_shipping_text = SHIPPING
    if not site.size_guide_note:
        site.size_guide_note = SIZE_NOTE
    site.save(update_fields=["product_shipping_text", "size_guide_note"])
    if not SizeChart.objects.exists():
        for order, (title, columns, rows) in enumerate(SIZE_CHARTS):
            SizeChart.objects.create(site=site, title=title, columns=columns, rows=rows, order=order)
    for slug, (title, body, items) in PAGES.items():
        page, created = Page.objects.get_or_create(slug=slug, defaults={"title": title, "body": body})
        if created:
            for order, (heading, text) in enumerate(items):
                PageItem.objects.create(page=page, heading=heading, body=text, order=order)


class Migration(migrations.Migration):
    dependencies = [("content", "0006_pages_and_product_texts")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
