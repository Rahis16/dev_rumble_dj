from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Count

#Permissions assigend to users
class Permission(models.Model):
    code = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)

    def __str__(self):
        return self.label

class Role(models.Model):
    ROLE_NAME_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('chef', 'Chef'),
        ('server', 'Server'),
        ('cashier', 'Cashier'),
        ('customer', 'Customer'),
        ('intern', 'Intern'),
        ('trainer', 'Trainer'),
        ('intern_manager', 'Intern Manager'),
    ]

    name = models.CharField(max_length=50, choices=ROLE_NAME_CHOICES, unique=True)
    permissions = models.ManyToManyField('Permission', related_name='roles')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_name_display()    
    

class UserProfile(models.Model):
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    lcid = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    section = models.CharField(max_length=50, null=True, blank=True)
    faculty = models.CharField(max_length=100, null=True, blank=True)
    program = models.CharField(max_length=100, null=True, blank=True)
    semester = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    orders_count = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.user.username
    
    @classmethod
    def top_by_order_type(cls, order_type='confirmed', limit=2):
        related_name_map = {
            'confirmed': 'user__confirmed_orders',
            'prepared': 'user__prepared_orders',
            'delivered': 'user__delivered_orders',
            'cancelled': 'user__cancelled_orders',
            'refunded': 'user__refunded_orders',
            # add more as needed
        }
        if order_type not in related_name_map:
            raise ValueError(f"Unsupported order type {order_type}")
    
        return (
            cls.objects
            .filter(role__name__in=['admin', 'manager', 'chef', 'server', 'cashier'])
            .annotate(order_count=Count(related_name_map[order_type]))
            .order_by('-order_count')[:limit]
        )
        
        #usage: top_profiles = UserProfile.top_by_order_type('delivered')
    
    

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username}'s Wallet"  
    
    
class TransactionHistory(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),  # Money added
        ('debit', 'Debit'),    # Money deducted
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    title = models.CharField(max_length=255)
    desc = models.TextField()  # Optional detailed description
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        direction = '+' if self.type == 'credit' else '-'
        return f"{self.wallet.user.username} {direction}${self.amount} - {self.title} on {self.created_at.strftime('%Y-%m-%d')}"      



# Category for better product grouping
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Categories"
        

# Product model with corrected price field
class Product(models.Model):
    name = models.CharField(max_length=255)
    desc = models.TextField(default="Product description")
    image = models.ImageField(upload_to='product_images/')
    price = models.DecimalField(max_digits=8, decimal_places=2)  # e.g., 99999.99
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)  # to easily disable products
    is_featured = models.BooleanField(default=False)  # for highlighting featured products
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name



# Improved Cart model
class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"

    class Meta:
        ordering = ['-created_at']


# Cart items (many-to-one with cart)
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # snapshot of unit price
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # quantity * price

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def save(self, *args, **kwargs):
        if self.price is None:
            self.price = self.product.price
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('cart', 'product')
        ordering = ['product__name']



class Table(models.Model):
    number = models.IntegerField(unique=True)
    capacity = models.IntegerField(default=4)
    is_occupied = models.BooleanField(default=False)  # Auto-update based on active orders

    def __str__(self):
        return f"Table {self.number}"

    def update_occupancy(self):
        # Count only 'preparing' orders for this table
        active_orders = self.orders.filter(status="pending").count()
        self.is_occupied = active_orders >= self.capacity - 1
        self.save()
        

# Order model (user, status, total, timestamp)
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PREPARE_DURATION_CHOICES = [
        (5, '5 minutes'),
        (10, '10 minutes'),
        (15, '15 minutes'),
        (20, '20 minutes'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    ordered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    prepare_duration = models.IntegerField(choices=PREPARE_DURATION_CHOICES, default=10)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, related_name="orders")
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="confirmed_orders")
    prepared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="prepared_orders")
    delivered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="delivered_orders")
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="cancelled_orders")
    refunded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="refunded_orders")
   

    def __str__(self):
        return f"Order #{self.pk} by {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Set confirmed_at when status is set to 'confirmed'
        if self.status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = timezone.now()

        # Set preparing_at when status is changed to 'preparing'
        if self.status == 'preparing' and not self.preparing_at:
            self.preparing_at = timezone.now()
            
        if self.table:
            self.table.update_occupancy()    

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-ordered_at']


# OrderItem: each item in the order
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product.name if self.product else 'Deleted Product'} @ {self.price}"

    class Meta:
        ordering = ['product__name']
        
        

class PaymentMethod(models.Model):
    METHOD_CHOICES = [
        ("wallet", "Wallet"),
        ("qr", "QR with Remarks"),
        ("counter", "On Counter Pay"),
    ]
    name = models.CharField(max_length=50, choices=METHOD_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()
            
        
class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")  # Link to the order
    method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    screenshot = models.ImageField(upload_to='payment_screenshots/', null=True, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("fake", "Fake Payment"),
    ], default="pending")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Rs.{self.amount} - {self.method.name} - {self.status}"   
    
    
    

#implemeneteation of real system now:

# Inventory Items
class InventoryItem(models.Model):
    item_name = models.CharField(max_length=100)
    quantity = models.FloatField(help_text="Enter in kg, L, or units")
    unit = models.CharField(max_length=20, default='kg')
    warning_level = models.CharField(
        max_length=20,
        choices=[('Good', 'Good'), ('Medium', 'Medium'), ('Low', 'Low'), ('Critical', 'Critical')],
        default='Good'
    )
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.item_name 
    

    



    
        
    
    
    
    
    