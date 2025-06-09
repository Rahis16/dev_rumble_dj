from django.db import models
from django.conf import settings
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    lcid = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    section = models.CharField(max_length=50, null=True, blank=True)
    faculty = models.CharField(max_length=100, null=True, blank=True)
    program = models.CharField(max_length=100, null=True, blank=True)
    semester = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.user.username
    
    
    
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username}'s Wallet"    



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


# Order model (user, status, total, timestamp)
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
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

    def __str__(self):
        return f"Order #{self.pk} by {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Set confirmed_at when status is set to 'confirmed'
        if self.status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = timezone.now()

        # Set preparing_at when status is changed to 'preparing'
        if self.status == 'preparing' and not self.preparing_at:
            self.preparing_at = timezone.now()

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
        ("failed", "Failed"),
    ], default="pending")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Rs.{self.amount} - {self.method.name} - {self.status}"        