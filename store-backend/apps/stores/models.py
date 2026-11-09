from django.db import models

from apps.core.models import TimeStampedModel


class Store(TimeStampedModel):
    name = models.CharField("نام شعبه", max_length=100)
    city = models.CharField("شهر", max_length=50, db_index=True)
    address = models.TextField("آدرس")
    phone = models.CharField("تلفن", max_length=30, blank=True)
    hours = models.CharField("ساعات کاری", max_length=100, blank=True)
    latitude = models.FloatField("عرض جغرافیایی", null=True, blank=True)
    longitude = models.FloatField("طول جغرافیایی", null=True, blank=True)
    image = models.ImageField("تصویر", upload_to="stores/", null=True, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "شعبه"
        verbose_name_plural = "شعب"
        ordering = ["order", "city", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.city})"
