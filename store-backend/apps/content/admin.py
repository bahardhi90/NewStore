from django.contrib import admin

from .models import Banner, FooterColumn, FooterLink, Page, PageItem, SiteSettings, SizeChart, TrustBadge


class TrustBadgeInline(admin.TabularInline):
    model = TrustBadge
    extra = 0
    fields = ["icon", "title", "subtitle", "is_active", "order"]


class SizeChartInline(admin.StackedInline):
    model = SizeChart
    extra = 0
    fields = ["title", "columns", "rows", "order"]


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ["brand_name", "tagline", "logo"]
    fieldsets = [
        (None, {"fields": ["brand_name", "tagline", "logo"]}),
        ("بالای سایت", {"fields": ["announcement_text"]}),
        ("شبکه‌های اجتماعی (در پاورقی)", {"fields": ["instagram_url", "telegram_url"]}),
        ("صفحه محصول", {"fields": ["product_shipping_text", "size_guide_note"]}),
    ]
    inlines = [TrustBadgeInline, SizeChartInline]

    def has_add_permission(self, request) -> bool:
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


class PageItemInline(admin.StackedInline):
    model = PageItem
    extra = 0
    fields = ["heading", "body", "order"]

    # What one item means on each page, so the admin knows what to type
    LABELS = {
        Page.Slug.FAQ: ("پرسش و پاسخ", "پرسش‌ها و پاسخ‌ها", "پرسش", "پاسخ"),
        Page.Slug.RETURNS: ("بخش", "بخش‌ها", "عنوان بخش", "متن"),
        Page.Slug.CONTACT: ("راه ارتباطی", "راه‌های ارتباطی", "عنوان (مثلاً تلفن پشتیبانی)", "مقدار"),
    }

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        labels = self.LABELS.get(obj.slug) if obj else None
        if labels:
            formset.form.base_fields["heading"].label = labels[2]
            formset.form.base_fields["body"].label = labels[3]
        if obj and obj.slug == Page.Slug.CONTACT:
            formset.form.base_fields["body"].help_text = "شماره تلفن و ایمیل خودکار قابل کلیک می‌شوند."
        return formset


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["__str__", "title", "updated_at"]
    fields = ["title", "body"]

    def get_inlines(self, request, obj):
        return [] if obj and obj.slug == Page.Slug.ABOUT else [PageItemInline]

    def get_inline_instances(self, request, obj=None):
        instances = super().get_inline_instances(request, obj)
        labels = PageItemInline.LABELS.get(obj.slug) if obj else None
        for inline in instances:
            if labels:
                inline.verbose_name, inline.verbose_name_plural = labels[0], labels[1]
        return instances

    def has_add_permission(self, request) -> bool:
        return False  # each page has a fixed address on the site

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 1
    fields = ["title", "url", "order"]


@admin.register(FooterColumn)
class FooterColumnAdmin(admin.ModelAdmin):
    list_display = ["title", "order"]
    list_editable = ["order"]
    fields = ["title", "order"]
    inlines = [FooterLinkInline]

    def save_model(self, request, obj, form, change) -> None:
        obj.site = SiteSettings.load()  # there is only one site
        super().save_model(request, obj, form, change)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["__str__", "link", "has_video", "is_active", "order"]
    list_editable = ["is_active", "order"]
    fields = ["title", "subtitle", "image", "image_mobile", "video", "link", "is_active", "order"]

    @admin.display(description="ویدیو", boolean=True)
    def has_video(self, obj: Banner) -> bool:
        return bool(obj.video)
