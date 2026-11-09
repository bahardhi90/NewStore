from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from .cache import invalidate_catalog_cache
from .models import Category, Collection, Product, ProductImage, Variant


@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=Collection)
@receiver([post_save, post_delete], sender=Product)
@receiver([post_save, post_delete], sender=ProductImage)
@receiver([post_save, post_delete], sender=Variant)
def _invalidate(sender, **kwargs) -> None:
    invalidate_catalog_cache()


@receiver(m2m_changed, sender=Product.collections.through)
def _invalidate_m2m(sender, **kwargs) -> None:
    invalidate_catalog_cache()
