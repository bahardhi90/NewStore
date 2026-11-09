from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from apps.core import messages as msg
from apps.core.utils import PHONE_RE, normalize_phone, to_en_digits

from .models import Address, User


class PhoneField(serializers.CharField):
    def to_internal_value(self, data):
        phone = normalize_phone(super().to_internal_value(data))
        if not PHONE_RE.match(phone):
            raise serializers.ValidationError(msg.PHONE_INVALID)
        return phone


class OtpRequestSerializer(serializers.Serializer):
    phone = PhoneField()


class OtpRequestResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    expires_in = serializers.IntegerField()
    resend_in = serializers.IntegerField()


class OtpVerifySerializer(serializers.Serializer):
    phone = PhoneField()
    code = serializers.CharField(max_length=6)

    def validate_code(self, value: str) -> str:
        value = to_en_digits(value).strip()
        if not value.isdigit() or len(value) != settings.OTP_LENGTH:
            raise serializers.ValidationError(msg.OTP_INVALID)
        return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "first_name", "last_name", "email", "date_joined"]
        read_only_fields = ["id", "phone", "date_joined"]


class AuthTokensSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
    is_new = serializers.BooleanField()


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class AddressSerializer(serializers.ModelSerializer):
    receiver_phone = PhoneField()

    class Meta:
        model = Address
        fields = [
            "id",
            "title",
            "receiver_name",
            "receiver_phone",
            "province",
            "city",
            "postal_code",
            "address_line",
            "is_default",
        ]

    def validate_postal_code(self, value: str) -> str:
        value = to_en_digits(value)
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(msg.POSTAL_CODE_INVALID)
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if self.instance is None and user.addresses.count() >= settings.MAX_ADDRESSES_PER_USER:
            raise serializers.ValidationError(msg.ADDRESS_LIMIT.format(count=settings.MAX_ADDRESSES_PER_USER))
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        user = self.context["request"].user
        is_first = not user.addresses.exists()
        instance = super().save(user=user, **kwargs)
        if is_first and not instance.is_default:
            instance.is_default = True
            instance.save(update_fields=["is_default"])
        if instance.is_default:
            user.addresses.exclude(pk=instance.pk).filter(is_default=True).update(is_default=False)
        return instance
