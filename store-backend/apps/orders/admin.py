import csv

from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponse

from apps.notifications.services import notify_order

from . import services
from .models import Order, OrderItem, OrderStatus, ShippingMethod


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ["title", "cost", "free_over", "is_active", "order"]
    list_editable = ["cost", "free_over", "is_active", "order"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = [
        "title",
        "size",
        "color",
        "sku",
        "quantity",
        "unit_price",
        "discount_percent",
        "final_unit_price",
        "line_total",
    ]
    readonly_fields = fields

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["number", "user", "status", "total", "shipping_title", "created_at", "paid_at"]
    list_filter = ["status", "created_at", "paid_at", "shipping_method"]
    search_fields = ["number", "user__phone", "user__last_name", "tracking_code"]
    list_select_related = ["user"]
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]
    readonly_fields = [
        "number",
        "user",
        "subtotal",
        "discount_total",
        "shipping_cost",
        "total",
        "shipping_method",
        "shipping_title",
        "address",
        "note",
        "expires_at",
        "paid_at",
        "stock_released",
        "created_at",
        "updated_at",
    ]
    fields = ["status", "tracking_code", *readonly_fields]
    actions = ["mark_processing", "mark_shipped", "mark_delivered", "cancel_orders", "export_csv"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and "status" in form.changed_data:
            notify_order(obj)

    def _set_status(self, request, queryset, new_status: str, allowed_from: list[str]) -> None:
        ids = list(queryset.filter(status__in=allowed_from).values_list("id", flat=True))
        updated = Order.objects.filter(id__in=ids).update(status=new_status)
        for order in Order.objects.filter(id__in=ids).select_related("user"):
            notify_order(order)  # customer SMS for the new status, if switched on in admin
        skipped = queryset.count() - updated
        self.message_user(request, f"{updated} سفارش به‌روزرسانی شد.", messages.SUCCESS)
        if skipped:
            self.message_user(request, f"{skipped} سفارش به دلیل وضعیت فعلی تغییر نکرد.", messages.WARNING)

    @admin.action(description="تغییر وضعیت به «در حال پردازش»")
    def mark_processing(self, request, queryset):
        self._set_status(request, queryset, OrderStatus.PROCESSING, [OrderStatus.PAID])

    @admin.action(description="تغییر وضعیت به «ارسال‌شده»")
    def mark_shipped(self, request, queryset):
        self._set_status(request, queryset, OrderStatus.SHIPPED, [OrderStatus.PAID, OrderStatus.PROCESSING])

    @admin.action(description="تغییر وضعیت به «تحویل‌شده»")
    def mark_delivered(self, request, queryset):
        self._set_status(request, queryset, OrderStatus.DELIVERED, [OrderStatus.SHIPPED])

    @admin.action(description="لغو سفارش و بازگرداندن موجودی")
    def cancel_orders(self, request, queryset):
        count = 0
        for order in queryset:
            with transaction.atomic():
                services.cancel_order(order.pk)
            count += 1
        self.message_user(
            request, f"{count} سفارش لغو شد. (سفارش‌های پرداخت‌شده را دستی استرداد کنید.)", messages.SUCCESS
        )

    @admin.action(description="خروجی CSV")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="orders.csv"'
        response.write("﻿")  # BOM so Excel shows Persian correctly
        writer = csv.writer(response)
        writer.writerow(
            ["شماره", "کاربر", "وضعیت", "جمع کالاها", "تخفیف", "ارسال", "مبلغ کل", "شهر", "تاریخ ثبت", "تاریخ پرداخت"]
        )
        for order in queryset.select_related("user"):
            writer.writerow(
                [
                    order.number,
                    order.user.phone,
                    order.get_status_display(),
                    order.subtotal,
                    order.discount_total,
                    order.shipping_cost,
                    order.total,
                    (order.address or {}).get("city", ""),
                    order.created_at.isoformat(),
                    order.paid_at.isoformat() if order.paid_at else "",
                ]
            )
        return response
