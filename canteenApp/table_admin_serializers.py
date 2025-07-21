# serializers. for tables in admin panel
from rest_framework import serializers
from .models import Table, Reservation, TableUpdateLog
from django.utils.timezone import localtime

class TableSerializer(serializers.ModelSerializer):
    customers = serializers.SerializerMethodField()
    orderValue = serializers.SerializerMethodField()
    seats = serializers.IntegerField(source="capacity")
    availableSeats = serializers.SerializerMethodField()
    timeOccupied = serializers.DateTimeField(source="occupied_at", format="%H:%M", allow_null=True)
    estimatedFinish = serializers.DateTimeField(source="estimated_finish", format="%H:%M", allow_null=True)
    areas = serializers.SerializerMethodField()


    class Meta:
        model = Table
        fields = ['id', 'number', 'seats', 'availableSeats', 'customers', 'area', 'areas', 'status', 'timeOccupied', 'estimatedFinish', 'orderValue']
    
    def get_orderValue(self, obj):
        return obj.order_value
    
    def get_areas(self, obj):
        return obj.get_areas()
    
    def get_customers(self, obj):
        active_orders = obj.orders.filter(status__in=["pending", "preparing"]).select_related("user")
        
        # Use a set to keep unique user IDs
        unique_users = {}
        for order in active_orders:
            user = order.user
            if user and user.id not in unique_users:
                unique_users[user.id] = user.get_full_name() or user.username
    
        return list(unique_users.values())
        
    def get_availableSeats(self, obj):
        active_orders = obj.orders.filter(status__in=["pending", "preparing"]).select_related("user")
    
        # Unique users count = assumed 1 seat per customer
        unique_user_ids = set()
        for order in active_orders:
            if order.user:
                unique_user_ids.add(order.user.id)
    
        occupied_seats = len(unique_user_ids)
        return max(obj.capacity - occupied_seats, 0)
    
        

class ReservationSerializer(serializers.ModelSerializer):
    tableNumber = serializers.IntegerField(source="table.number")

    class Meta:
        model = Reservation
        fields = ['id', 'customer_name', 'phone', 'email', 'date', 'time', 'guests', 'tableNumber', 'status', 'special_requests', 'created_at']


class TableUpdateLogSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()

    class Meta:
        model = TableUpdateLog
        fields = ['id', 'time', 'message', 'type']

    def get_time(self, obj):
        return localtime(obj.created_at).strftime('%H:%M')