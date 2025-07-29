from django.contrib import admin
from .models import Product, Category, Cart, CartItem, Order, OrderItem, UserProfile, Wallet, Payment, PaymentMethod, Table, TransactionHistory, InventoryItem, Role, Permission, Reservation, Notification


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'full_name',
        'lcid',
        'phone_number',
        'section',
        'faculty',
        'program',
    )
    search_fields = ('user__username', 'full_name', 'lcid', 'phone_number')
    list_filter = ('faculty', 'program', 'section')
    # readonly_fields = ('user',)
    
    
# Admin for Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# Admin for Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category')
    search_fields = ('name',)
    list_filter = ('category',)



from django.contrib import admin
from .models import Cart, CartItem

# Inline display for CartItem inside Cart
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity')
    can_delete = False


# Admin for Cart
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    inlines = [CartItemInline]
    readonly_fields = ('created_at',)

    def has_add_permission(self, request):
        # Carts are created automatically, not via admin
        return False


# Admin for CartItem
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'product', 'quantity', 'cart')
    search_fields = ('cart__user__username', 'product__name')
    list_filter = ('product',)
    ordering = ('cart__user__username', 'product__name')

    def get_user(self, obj):
        return obj.cart.user.username if obj.cart.user else "-"
    get_user.short_description = 'User'



# Admin for Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'ordered_at', 'status', 'total_price')
    list_filter = ('status',)
    search_fields = ('user__username',)


# Admin for OrderItem
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__user__username', 'product__name')
    
    
    
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username',)

    # def has_add_permission(self, request):
    #     # Wallets are created automatically, not via admin
    #     return False    
    
    
@admin.register(TransactionHistory)
class TransactionHistoryAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'type', 'amount', 'created_at')
    search_fields = ('wallet__user__username', 'type')
    list_filter = ('type',)
    ordering = ('-created_at',)

    # def has_add_permission(self, request):
    #     # Transaction history is managed automatically, not via admin
    #     return False    


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'method', 'created_at')
    search_fields = ('user__username', 'method__name')
    list_filter = ('method',)
    ordering = ('-created_at',)
    
    
    
@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

    # def has_add_permission(self, request):
    #     # Payment methods are predefined, not added via admin
    #     return False  
    
    
# @admin.register(Table)
# class TableAdmin(admin.ModelAdmin):
#     list_display = ('number', 'capacity', 'is_occupied', 'occupied_seats')
#     list_editable = ('capacity',)
#     list_filter = ('is_occupied',)
#     search_fields = ('number',)

#     def occupied_seats(self, obj):
#         return obj.orders.filter(status='preparing').count()
#     occupied_seats.short_description = 'Occupied Seats' 

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = (
        'number',
        'capacity',
        'status',
        'area',
        'occupied_at',
        'estimated_finish',
        'order_value_display',
    )
    list_filter = ('status', 'area')
    search_fields = ('number',)
    ordering = ('number',)

    @admin.display(description="Order Value (Active)")
    def order_value_display(self, obj):
        return f"Rs. {obj.order_value:.2f}" 
    
    
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'table', 'date', 'time', 'guests', 'status')
    search_fields = ('customer_name', 'phone', 'email')
    list_filter = ('status', 'date')
     
    
    

# Customize InventoryItem admin
@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'quantity', 'unit', 'warning_level', 'last_updated')
    list_filter = ('warning_level', 'unit')
    search_fields = ('item_name',)       
    
    
    
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    
    
    
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'label')
    search_fields = ('code', 'label')    
    
    
    

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'icon', 'unread', 'time')
    list_filter = ('icon', 'unread', 'time')
    search_fields = ('title', 'message')
    ordering = ('-time',)
    readonly_fields = ('time',)    