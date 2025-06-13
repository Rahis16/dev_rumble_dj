from rest_framework import serializers
from .models import Product, Category, CartItem, Order, OrderItem, UserProfile, Payment
from allauth.account.adapter import get_adapter
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
  
  
class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = UserProfile
        fields = '__all__'  # 'user' is linked automatically via request.user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']  # Add more fields if your model has them    

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


#product serializer for admin view
class ProductSerializerAdmin(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    image = serializers.ImageField(required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'desc', 'price', 'image', 'category', 'is_active',
            'is_featured', 'created_at', 'category_name'
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'quantity',
            'price',        # unit price snapshot from CartItem.price
            'total_price',  # quantity * price from CartItem.total_price
            'product_name',
            'product_image',
        ]

    def get_product_image(self, obj):
        request = self.context.get('request')
        if obj.product.image and hasattr(obj.product.image, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.product.image.url)
            else:
                return obj.product.image.url
        return None
    
    
    
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'ordered_at', 'status', 'confirmed_at', 'preparing_at', 'prepare_duration', 'total_price', 'items']  
        
        
        

#used in getting sigle order details in admin view
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'method', 'amount', 'screenshot', 'remarks', 'paid_at', 'status']
        
    def get_screenshot(self, obj):
        request = self.context.get('request')
        if obj.screenshot and request:
            return request.build_absolute_uri(obj.screenshot.url)
        elif obj.screenshot:
            return obj.screenshot.url
        return None    
        
class OrderItemSerializer2(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'quantity', 'price']

    def get_product_name(self, obj):
        return obj.product.name if obj.product else "Deleted Product"
    

#used in getting sigle order details in admin view
class OrderSerializer2(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    items = OrderItemSerializer(many=True, read_only=True)
    table_number = serializers.SerializerMethodField()
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'total_price', 'ordered_at', 
            'confirmed_at', 'preparing_at', 'prepare_duration',
            'table_number', 'items', 'payment'
        ]

    def get_table_number(self, obj):
        return obj.table.number if obj.table else None          