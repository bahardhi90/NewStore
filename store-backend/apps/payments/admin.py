from django import forms
from django.conf import settings
from django.contrib import admin

from .models import Payment, PaymentCode, PaymentMethod

SECRET_HELP = "برای حفظ مقدار قبلی، خالی بگذارید."


class PaymentMethodForm(forms.ModelForm):
    """Secrets are never shown again after saving; leaving the box empty keeps the stored value."""

    password = forms.CharField(
        label="رمز عبور", required=False, help_text=SECRET_HELP, widget=forms.PasswordInput(render_value=False)
    )
    client_secret = forms.CharField(
        label="Client Secret", required=False, help_text=SECRET_HELP, widget=forms.PasswordInput(render_value=False)
    )

    class Meta:
        model = PaymentMethod
        fields = "__all__"

    def clean_password(self) -> str:
        return self.cleaned_data["password"] or self.instance.password

    def clean_client_secret(self) -> str:
        return self.cleaned_data["client_secret"] or self.instance.client_secret


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    form = PaymentMethodForm
    list_display = ["title", "code", "is_active", "order", "connection_status"]
    list_editable = ["is_active", "order"]
    readonly_fields = ["code"]

    def get_queryset(self, request):
        methods = super().get_queryset(request)
        if settings.PAYMENT_GATEWAY != PaymentCode.FAKE:
            methods = methods.exclude(code=PaymentCode.FAKE)
        return methods

    def get_fieldsets(self, request, obj=None):
        general = ("code", "is_active", "title", "description", "logo", "order", "min_amount", "max_amount")
        if obj and obj.code == PaymentCode.ZARINPAL:
            connection = ("merchant_id", "sandbox")
        elif obj and obj.code == PaymentCode.DIGIPAY:
            connection = ("username", "password", "client_id", "client_secret", "category", "sandbox", "api_url")
        elif obj and obj.code == PaymentCode.SNAPPPAY:
            connection = ("username", "password", "client_id", "client_secret", "category", "api_url")
        else:
            return [(None, {"fields": general})]
        return [(None, {"fields": general}), ("اطلاعات اتصال به درگاه", {"fields": connection})]

    @admin.display(description="اطلاعات اتصال", boolean=True)
    def connection_status(self, obj: PaymentMethod) -> bool:
        return not obj.missing_credentials()

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["order", "amount", "gateway", "status", "ref_id", "needs_refund", "created_at"]
    list_filter = ["status", "gateway", "needs_refund", "created_at"]
    search_fields = ["order__number", "authority", "ref_id", "order__user__phone"]
    list_select_related = ["order"]
    readonly_fields = [
        "order",
        "amount",
        "gateway",
        "authority",
        "ref_id",
        "card_pan",
        "status",
        "raw_request",
        "raw_response",
        "verified_at",
        "created_at",
    ]
    fields = [*readonly_fields, "needs_refund"]

    def has_add_permission(self, request) -> bool:
        return False
