from rest_framework import serializers

from .models import PaymentMethod


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["code", "title", "description", "logo", "min_amount", "max_amount"]


class PaymentStartSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    method = serializers.CharField(max_length=30, required=False)


class PaymentStartResponseSerializer(serializers.Serializer):
    redirect_url = serializers.URLField()
    payment_id = serializers.IntegerField()


class PaymentVerifyQuerySerializer(serializers.Serializer):
    Authority = serializers.CharField(max_length=100)
    Status = serializers.CharField(max_length=20)
    TrackingCode = serializers.CharField(max_length=100, required=False, allow_blank=True)
    Type = serializers.CharField(max_length=10, required=False, allow_blank=True)


class PaymentVerifyResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["success", "failed", "cancelled"])
    detail = serializers.CharField()
    order_id = serializers.IntegerField(allow_null=True)
    order_number = serializers.CharField(allow_null=True)
    ref_id = serializers.CharField(allow_null=True)
    amount = serializers.IntegerField(allow_null=True)
