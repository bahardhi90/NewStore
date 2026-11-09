"""Cache keys + invalidation for catalog/home data."""

from django.core.cache import cache

CATEGORIES_KEY = "catalog:categories:v1"
HOME_KEY = "content:home:v1"


def invalidate_catalog_cache() -> None:
    cache.delete_many([CATEGORIES_KEY, HOME_KEY])
