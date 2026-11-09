from django.contrib import admin

from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "phone", "is_active", "order"]
    list_editable = ["is_active", "order"]
    list_filter = ["city", "is_active"]
    search_fields = ["name", "city", "address"]
