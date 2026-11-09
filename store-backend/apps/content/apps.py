from django.apps import AppConfig


class ContentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.content"
    label = "content"
    verbose_name = "محتوا"

    def ready(self) -> None:
        from django.db.models.signals import post_delete, post_save

        from apps.catalog.cache import invalidate_catalog_cache

        from .models import Banner

        def _invalidate(sender, **kwargs) -> None:
            invalidate_catalog_cache()

        post_save.connect(_invalidate, sender=Banner, dispatch_uid="banner_save_cache")
        post_delete.connect(_invalidate, sender=Banner, dispatch_uid="banner_delete_cache")
