from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.utils.html import format_html

from .models import Category, Collection, Product, ProductImage, Variant


class DiscountActionForm(ActionForm):
    discount_percent = forms.IntegerField(
        label="درصد تخفیف", required=False, min_value=0, max_value=90, help_text="برای اکشن «اعمال تخفیف»"
    )


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    fields = ["size", "color", "color_hex", "stock", "sku"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["preview", "image", "color", "alt", "order"]
    readonly_fields = ["preview"]

    def get_formset(self, request, obj=None, **kwargs):
        """Color is a dropdown of the product's own colors, so it always matches a color button."""
        formset = super().get_formset(request, obj, **kwargs)
        colors = list(obj.variants.order_by().values_list("color", flat=True).distinct()) if obj else []
        field = formset.form.base_fields["color"]
        if colors:
            field.widget = forms.Select(choices=[("", "همه رنگ‌ها"), *[(c, c) for c in sorted(colors)]])
        else:
            field.help_text = "ابتدا تنوع‌ها (رنگ‌ها) را ذخیره کنید تا فهرست رنگ‌ها اینجا نمایش داده شود."
        return formset

    @admin.display(description="پیش‌نمایش")
    def preview(self, obj: ProductImage) -> str:
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:4px" />', obj.image.url)
        return "-"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "order", "is_active"]
    list_editable = ["order", "is_active"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "is_active", "is_featured", "order"]
    list_editable = ["is_active", "is_featured", "order"]
    search_fields = ["title", "slug"]
    prepopulated_fields = {"slug": ["title"]}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "base_price", "discount_percent", "final_price", "total_stock", "is_active"]
    list_filter = ["is_active", "category", "collections", "created_at"]
    list_editable = ["is_active"]
    search_fields = ["title", "slug", "variants__sku"]
    prepopulated_fields = {"slug": ["title"]}
    readonly_fields = ["final_price", "sales_count", "created_at", "updated_at"]
    filter_horizontal = ["collections"]
    inlines = [VariantInline, ProductImageInline]
    list_select_related = ["category"]
    action_form = DiscountActionForm
    actions = ["apply_discount", "remove_discount", "activate", "deactivate"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("variants")

    @admin.display(description="موجودی کل")
    def total_stock(self, obj: Product) -> int:
        return sum(v.stock for v in obj.variants.all())

    @admin.action(description="اعمال تخفیف (درصد را در کادر بالا وارد کنید)")
    def apply_discount(self, request, queryset):
        raw = request.POST.get("discount_percent")
        try:
            percent = int(raw)
        except (TypeError, ValueError):
            self.message_user(request, "درصد تخفیف را وارد کنید.", messages.ERROR)
            return
        if not 0 <= percent <= 90:
            self.message_user(request, "درصد تخفیف باید بین ۰ و ۹۰ باشد.", messages.ERROR)
            return
        count = 0
        for product in queryset:
            product.discount_percent = percent
            product.save(update_fields=["discount_percent", "updated_at"])
            count += 1
        self.message_user(request, f"تخفیف {percent}٪ روی {count} محصول اعمال شد.", messages.SUCCESS)

    @admin.action(description="حذف تخفیف")
    def remove_discount(self, request, queryset):
        for product in queryset:
            product.discount_percent = 0
            product.save(update_fields=["discount_percent", "updated_at"])
        self.message_user(request, "تخفیف حذف شد.", messages.SUCCESS)

    @admin.action(description="فعال‌سازی")
    def activate(self, request, queryset):
        for product in queryset:
            product.is_active = True
            product.save(update_fields=["is_active", "updated_at"])

    @admin.action(description="غیرفعال‌سازی")
    def deactivate(self, request, queryset):
        for product in queryset:
            product.is_active = False
            product.save(update_fields=["is_active", "updated_at"])


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ["product", "size", "color", "stock", "sku"]
    list_filter = ["size", "color"]
    list_editable = ["stock"]
    search_fields = ["sku", "product__title"]
    list_select_related = ["product"]
