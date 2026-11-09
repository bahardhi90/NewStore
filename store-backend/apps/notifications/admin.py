from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html, format_html_join

from .models import SmsLog, SmsSettings, SmsTemplate
from .providers import SmsError
from .services import send_now

PANEL_STEPS = (
    "این متن را در پنل ملی پیامک ثبت کنید: ابزار ویژه ← وبسرویس خدماتی ← «+ درج متن جدید». "
    "ملی پیامک آدرس سایت را در انتهای متن لازم می‌داند. پس از تأیید، کد پترن را در کادر پایین وارد کنید."
)


class SmsSettingsForm(forms.ModelForm):
    password = forms.CharField(
        label="رمز عبور / کلید API ملی پیامک",
        required=False,
        help_text="برای حفظ مقدار قبلی، خالی بگذارید.",
        widget=forms.PasswordInput(render_value=False),
    )

    class Meta:
        model = SmsSettings
        fields = ["provider", "username", "password", "api_url"]

    def clean_password(self) -> str:
        return self.cleaned_data["password"] or self.instance.password


@admin.register(SmsSettings)
class SmsSettingsAdmin(admin.ModelAdmin):
    form = SmsSettingsForm
    list_display = ["__str__", "provider", "username"]
    fieldsets = [
        (None, {"fields": ["provider"]}),
        ("اطلاعات ورود به ملی پیامک", {"fields": ["username", "password", "api_url"]}),
    ]

    def has_add_permission(self, request) -> bool:
        return not SmsSettings.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(SmsTemplate)
class SmsTemplateAdmin(admin.ModelAdmin):
    list_display = ["__str__", "is_active", "body_id", "text"]
    list_editable = ["is_active", "body_id"]
    readonly_fields = ["event", "allowed_variables", "pattern_text_for_panel"]
    fields = ["event", "is_active", "text", "allowed_variables", "pattern_text_for_panel", "body_id"]
    actions = ["send_test"]

    @admin.display(description="متغیرهای قابل استفاده")
    def allowed_variables(self, obj: SmsTemplate):
        return format_html(
            "<ul style='margin:0;padding-inline-start:1.2em'>{}</ul>",
            format_html_join("", "<li><code>{{{}}}</code> — {}</li>", obj.spec.variables.items()),
        )

    @admin.display(description="متن برای ثبت در ملی پیامک")
    def pattern_text_for_panel(self, obj: SmsTemplate):
        return format_html(
            "<code style='display:block;white-space:pre-wrap;padding:.5em;direction:rtl'>{}</code>"
            "<p class='help'>{}</p>",
            obj.pattern_text,
            PANEL_STEPS,
        )

    @admin.action(description="ارسال پیامک آزمایشی به شماره خودم")
    def send_test(self, request, queryset):
        phone = request.user.phone
        for template in queryset:
            try:
                send_now(template.event, phone, template.spec.sample, template=template)
            except SmsError as exc:
                self.message_user(request, f"«{template}»: {exc}", messages.ERROR)
            else:
                self.message_user(request, f"«{template}» به {phone} ارسال شد.", messages.SUCCESS)

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "event", "phone", "status", "provider", "detail"]
    list_filter = ["status", "event", "provider", "created_at"]
    search_fields = ["phone", "text"]
    readonly_fields = ["created_at", "event", "phone", "text", "provider", "status", "detail"]
    fields = readonly_fields

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
