from django.conf import settings
from django.db import models

from apps.catalog.models import Variant
from apps.core.models import TimeStampedModel


class Cart(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")

    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"

    def __str__(self) -> str:
        return f"سبد {self.user}"


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveSmallIntegerField("تعداد", default=1)

    class Meta:
        verbose_name = "آیتم سبد"
        verbose_name_plural = "آیتم‌های سبد"
        ordering = ["created_at", "id"]
        constraints = [models.UniqueConstraint(fields=["cart", "variant"], name="unique_variant_per_cart")]

    def __str__(self) -> str:
        return f"{self.variant} × {self.quantity}"
