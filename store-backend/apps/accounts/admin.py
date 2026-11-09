from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Address, User


class AddressInline(admin.StackedInline):
    model = Address
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["phone", "first_name", "last_name", "is_active", "is_staff", "date_joined"]
    list_filter = ["is_active", "is_staff", "date_joined"]
    search_fields = ["phone", "first_name", "last_name", "email"]
    inlines = [AddressInline]
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("اطلاعات شخصی", {"fields": ("first_name", "last_name", "email")}),
        ("دسترسی‌ها", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("تاریخ‌ها", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("phone", "password1", "password2")}),)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "city", "receiver_name", "is_default"]
    search_fields = ["user__phone", "receiver_name", "city", "postal_code"]
    list_select_related = ["user"]
