import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.content.models import MAX_VIDEO_MB, Banner, FooterColumn, SiteSettings, TrustBadge

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(client):
    client.force_login(get_user_model().objects.create_superuser("09120000000", "password"))
    return client


def test_site_settings_returns_everything_the_header_and_footer_show(api_client):
    body = api_client.get("/api/site-settings/").json()
    assert body["brand_name"] == "کرامت"
    assert body["logo"] is None
    assert body["announcement_text"] == "ارسال رایگان برای خریدهای بالای ۳ میلیون تومان"
    assert body["instagram_url"] == "https://instagram.com"
    assert [b["icon"] for b in body["trust_badges"]] == ["return", "truck", "shield", "badge"]
    assert [c["title"] for c in body["footer_columns"]] == ["راهنمای خرید", "فروشگاه"]
    assert body["footer_columns"][0]["links"][0] == {"title": "سوالات متداول", "url": "/faq"}


def test_admin_changes_show_up(api_client):
    site = SiteSettings.load()
    site.announcement_text = ""
    site.save()
    TrustBadge.objects.filter(icon="truck").update(is_active=False)
    FooterColumn.objects.filter(title="فروشگاه").delete()
    body = api_client.get("/api/site-settings/").json()
    assert body["announcement_text"] == ""
    assert "truck" not in [b["icon"] for b in body["trust_badges"]]
    assert [c["title"] for c in body["footer_columns"]] == ["راهنمای خرید"]


def test_site_settings_query_count_is_constant(api_client, django_assert_max_num_queries):
    with django_assert_max_num_queries(6):
        api_client.get("/api/site-settings/")


def test_banner_needs_an_image_or_a_video():
    with pytest.raises(ValidationError):
        Banner(title="x").full_clean()


def test_banner_accepts_mp4_without_an_image(api_client):
    banner = Banner(title="x", video=SimpleUploadedFile("clip.mp4", b"\x00" * 1024, content_type="video/mp4"))
    banner.full_clean()
    banner.save()
    item = api_client.get("/api/home/").json()["banners"][0]
    assert item["video"].endswith(".mp4")
    assert item["image"] is None


@pytest.mark.parametrize(
    ("name", "size"),
    [("clip.mov", 1024), ("clip.mp4", MAX_VIDEO_MB * 1024 * 1024 + 1)],
)
def test_banner_rejects_other_formats_and_large_videos(name, size):
    banner = Banner(title="x", video=SimpleUploadedFile(name, b"\x00" * size))
    with pytest.raises(ValidationError):
        banner.full_clean()


def test_home_cache_is_cleared_when_a_banner_changes(api_client):
    assert api_client.get("/api/home/").json()["banners"] == []
    Banner.objects.create(title="new", video="banners/videos/a.mp4")
    assert len(api_client.get("/api/home/").json()["banners"]) == 1


def test_admin_pages_open(admin_client):
    column = FooterColumn.objects.first()
    for url in [
        "/admin/content/sitesettings/1/change/",
        "/admin/content/footercolumn/",
        f"/admin/content/footercolumn/{column.pk}/change/",
        "/admin/content/footercolumn/add/",
        "/admin/content/banner/add/",
    ]:
        assert admin_client.get(url).status_code == 200, url


def test_product_image_color_is_a_dropdown_of_the_products_colors(admin_client, api_client):
    from .factories import ProductImageFactory, VariantFactory

    variant = VariantFactory(color="سفید")
    VariantFactory(product=variant.product, color="مشکی", size="XL")
    ProductImageFactory(product=variant.product, color="مشکی")
    page = admin_client.get(f"/admin/catalog/product/{variant.product.pk}/change/").content.decode()
    assert '<option value="مشکی">مشکی</option>' in page
    assert '<option value="سفید">سفید</option>' in page
    body = api_client.get(f"/api/products/{variant.product.slug}/").json()
    assert body["images"][0]["color"] == "مشکی"


def test_product_page_texts_come_from_site_settings(api_client):
    body = api_client.get("/api/site-settings/").json()
    assert body["shipping_points"][2] == "تعویض سایز رایگان است."
    assert body["size_guide_note"].startswith("اندازه‌ها به سانتی‌متر است")
    tops, pants = body["size_charts"]
    assert tops["columns"] == ["سایز", "دور سینه", "قد", "سرشانه تا سرآستین"]
    assert tops["rows"][0] == ["S", "۹۶–۱۰۰", "۷۰", "۶۲"]
    assert pants["rows"][-1] == ["۳۸", "۹۶", "۱۰۶"]


@pytest.mark.parametrize(
    ("slug", "paragraphs", "items"),
    [("about", 3, 0), ("contact", 1, 4), ("faq", 0, 6), ("returns", 0, 4)],
)
def test_pages_keep_their_current_text(api_client, slug, paragraphs, items):
    body = api_client.get(f"/api/pages/{slug}/").json()
    assert body["slug"] == slug
    assert len(body["paragraphs"]) == paragraphs
    assert len(body["items"]) == items


def test_unknown_page_is_404(api_client):
    assert api_client.get("/api/pages/nope/").status_code == 404


def test_size_chart_rows_must_match_the_columns():
    from apps.content.models import SizeChart

    chart = SizeChart(site=SiteSettings.load(), title="t", columns="سایز، قد", rows="S، ۷۰\nM")
    with pytest.raises(ValidationError) as error:
        chart.full_clean()
    assert "ردیف 2" in str(error.value)
    chart.rows = "S, 70\nM | 72"  # comma, Persian comma and | all work
    chart.full_clean()
    assert chart.row_list == [["S", "70"], ["M", "72"]]


@pytest.mark.parametrize(("slug", "label"), [("about", None), ("faq", "پرسش"), ("contact", "راه ارتباطی")])
def test_page_admin_shows_what_to_type(admin_client, slug, label):
    from apps.content.models import Page

    page = Page.objects.get(slug=slug)
    html = admin_client.get(f"/admin/content/page/{page.pk}/change/").content.decode()
    assert 'name="title"' in html
    if label:
        assert label in html
    else:
        assert "items-TOTAL_FORMS" not in html
    assert admin_client.get("/admin/content/page/add/").status_code == 403


def test_new_footer_column_from_admin_belongs_to_the_site(admin_client):
    data = {
        "title": "شبکه‌ها",
        "order": 5,
        "links-TOTAL_FORMS": 1,
        "links-INITIAL_FORMS": 0,
        "links-0-title": "وبلاگ",
        "links-0-url": "/blog",
        "links-0-order": 0,
    }
    response = admin_client.post("/admin/content/footercolumn/add/", data)
    assert response.status_code == 302, response.content.decode()[:500]
    column = FooterColumn.objects.get(title="شبکه‌ها")
    assert column.site_id == 1
    assert column.links.get().url == "/blog"
