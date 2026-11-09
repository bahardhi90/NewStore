import pytest

from .factories import (
    CategoryFactory,
    CollectionFactory,
    ProductFactory,
    ProductImageFactory,
    VariantFactory,
)

pytestmark = pytest.mark.django_db


def slugs(response) -> set[str]:
    return {p["slug"] for p in response.json()["results"]}


def test_product_list_shape(api_client):
    product = ProductFactory(base_price=2_000_000, discount_percent=25)
    ProductImageFactory(product=product)
    ProductImageFactory(product=product)
    response = api_client.get("/api/products/")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"count", "next", "previous", "results"}
    item = body["results"][0]
    assert set(item) == {"id", "title", "slug", "image", "hover_image", "base_price", "discount_percent", "final_price"}
    assert item["final_price"] == 1_500_000
    assert item["image"].startswith("http")
    assert item["hover_image"].startswith("http")


def test_inactive_products_hidden(api_client):
    ProductFactory(slug="visible")
    ProductFactory(slug="hidden", is_active=False)
    assert slugs(api_client.get("/api/products/")) == {"visible"}
    assert api_client.get("/api/products/hidden/").status_code == 404


def test_filter_by_category_includes_children(api_client):
    parent = CategoryFactory(slug="jackets")
    child = CategoryFactory(slug="vests", parent=parent)
    other = CategoryFactory(slug="pants")
    ProductFactory(slug="a", category=parent)
    ProductFactory(slug="b", category=child)
    ProductFactory(slug="c", category=other)
    assert slugs(api_client.get("/api/products/?category=jackets")) == {"a", "b"}


def test_filter_collection_on_sale_and_price(api_client):
    spring = CollectionFactory(slug="spring")
    cheap = ProductFactory(slug="cheap", base_price=500_000, discount_percent=10)
    cheap.collections.add(spring)
    ProductFactory(slug="expensive", base_price=5_000_000)
    assert slugs(api_client.get("/api/products/?collection=spring")) == {"cheap"}
    assert slugs(api_client.get("/api/products/?on_sale=true")) == {"cheap"}
    assert slugs(api_client.get("/api/products/?min_price=1000000")) == {"expensive"}
    assert slugs(api_client.get("/api/products/?max_price=1000000")) == {"cheap"}


def test_filter_size_and_color_only_in_stock(api_client):
    VariantFactory(product__slug="l-black", size="L", color="مشکی", stock=3)
    VariantFactory(product__slug="m-white", size="M", color="سفید", stock=3)
    VariantFactory(product__slug="l-soldout", size="L", color="مشکی", stock=0)
    assert slugs(api_client.get("/api/products/?size=L")) == {"l-black"}
    assert slugs(api_client.get("/api/products/?size=L,M")) == {"l-black", "m-white"}
    assert slugs(api_client.get("/api/products/?color=سفید")) == {"m-white"}


def test_ordering(api_client):
    ProductFactory(slug="p1", base_price=3_000_000)
    ProductFactory(slug="p2", base_price=1_000_000)
    ProductFactory(slug="p3", base_price=2_000_000, discount_percent=60)
    order = [p["slug"] for p in api_client.get("/api/products/?ordering=price").json()["results"]]
    assert order == ["p3", "p2", "p1"]
    order = [p["slug"] for p in api_client.get("/api/products/?ordering=-price").json()["results"]]
    assert order == ["p1", "p2", "p3"]


def test_search(api_client):
    ProductFactory(slug="shirt", title="پیراهن آکسفورد")
    ProductFactory(slug="pants", title="شلوار جین")
    assert slugs(api_client.get("/api/products/?search=آکسفورد")) == {"shirt"}


def test_product_detail(api_client):
    variant = VariantFactory(product__slug="detail", stock=0)
    ProductImageFactory(product=variant.product)
    body = api_client.get("/api/products/detail/").json()
    assert body["category"]["slug"] == variant.product.category.slug
    assert body["variants"] == [{"id": variant.id, "size": "L", "color": "مشکی", "color_hex": "#000000", "stock": 0}]
    assert len(body["images"]) == 1


def test_filter_options(api_client):
    cat = CategoryFactory(slug="shirts")
    VariantFactory(product__category=cat, product__base_price=1_000_000, size="M", color="سفید", color_hex="#fff")
    VariantFactory(product__category=cat, product__base_price=3_000_000, size="XL", color="مشکی")
    VariantFactory(product__category=cat, size="S", color="قرمز", stock=0)
    VariantFactory(product__category=cat, size="M", color="مشکی")  # same size on another product: listed once
    body = api_client.get("/api/products/filters/?category=shirts").json()
    assert body["sizes"] == ["M", "XL"]
    assert {c["name"] for c in body["colors"]} == {"سفید", "مشکی"}
    assert body["min_price"] == 1_000_000
    assert body["max_price"] == 3_000_000


def test_product_list_query_count_is_constant(api_client, django_assert_max_num_queries):
    for _ in range(10):
        product = ProductFactory()
        ProductImageFactory(product=product)
        ProductImageFactory(product=product)
    with django_assert_max_num_queries(3):
        response = api_client.get("/api/products/")
    assert response.status_code == 200


def test_product_detail_query_count(api_client, django_assert_max_num_queries):
    variant = VariantFactory(product__slug="q")
    variant.product.collections.add(CollectionFactory())
    ProductImageFactory(product=variant.product)
    with django_assert_max_num_queries(5):
        assert api_client.get("/api/products/q/").status_code == 200


def test_categories_and_collections(api_client):
    CategoryFactory(slug="jackets")
    CollectionFactory(slug="spring")
    assert [c["slug"] for c in api_client.get("/api/categories/").json()] == ["jackets"]
    assert api_client.get("/api/collections/spring/").json()["slug"] == "spring"


def test_home_and_cache_invalidation(api_client):
    ProductFactory(slug="old", discount_percent=10)
    body = api_client.get("/api/home/").json()
    assert set(body) == {"banners", "categories", "on_sale", "collection_highlight", "newest"}
    assert [p["slug"] for p in body["on_sale"]] == ["old"]
    ProductFactory(slug="new", discount_percent=30)
    body = api_client.get("/api/home/").json()
    assert [p["slug"] for p in body["on_sale"]] == ["new", "old"]
