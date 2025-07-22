# payments/serializers.py
from rest_framework import serializers
from .models import Payment
from django.utils.timezone import localtime

class PaymentSerializerAdmin(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    payment_method = serializers.CharField(source="method.name", read_only=True)
    transaction_id = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "order_id",
            "amount",
            "payment_method",
            "status",
            "transaction_id",
            "created_at",
        ]

    def get_transaction_id(self, obj):
        return f"TXN{obj.id:06d}"
    
    def get_created_at(self, obj):
        local_dt = localtime(obj.created_at)
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")