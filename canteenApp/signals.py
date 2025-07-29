from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
# from django.contrib.auth.models import User
from django.conf import settings
from .models import UserProfile, Wallet, Permission, Role,  Table, Reservation, Order, TableUpdateLog as UpdateLog, Notification
from django.db.models.signals import post_migrate


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_superuser:
            role_name = 'admin'
        else:
            role_name = 'customer'

        # Get or create the role
        role, _ = Role.objects.get_or_create(name=role_name)

        # Assign permissions
        if instance.is_superuser:
            # Assign all permissions to admin
            all_perms = Permission.objects.all()
            role.permissions.set(all_perms)
        else:
            # Ensure 'use_client_panel' permission exists
            permission, _ = Permission.objects.get_or_create(
                code='use_client_panel',
                defaults={'label': 'Use Client Panel'}
            )
            if not role.permissions.filter(code=permission.code).exists():
                role.permissions.add(permission)

        # Create the user profile with the correct role
        UserProfile.objects.create(user=instance, role=role)
        

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def sync_user_profile_status(sender, instance, **kwargs):
    try:
        profile = instance.profile  # This uses related_name='profile'
        profile.status = 'active' if instance.is_active else 'inactive'
        profile.save()
    except UserProfile.DoesNotExist:
        # In case profile not created yet
        pass        
        
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)        
        
        
        

@receiver(post_migrate)
def create_default_permissions(sender, **kwargs):
    predefined_permissions = [
        ('use_client_panel', 'Use Client Panel'),
        ('view_dashboard', 'View Dashboard'),
        ('manage_users', 'Manage Users'),
        ('view_users', 'View Users'),
        ('manage_products', 'Manage Products'),
        ('view_products', 'View Products'),
        ('manage_orders', 'Manage Orders'),
        ('view_orders', 'View Orders'),
        ('manage_inventory', 'Manage Inventory'),
        ('view_inventory', 'View Inventory'),
        ('manage_roles', 'Manage Roles'),
        ('view_roles', 'View Roles'),
        ('manage_settings', 'Manage Settings'),
        ('view_settings', 'View Settings'),
        ('manage_reports', 'Manage Reports'),
        ('view_reports', 'View Reports'),
        ('manage_notifications', 'Manage Notifications'),
        ('view_notifications', 'View Notifications'),
        ('manage_staff', 'Manage Staff'),
        ('view_staff', 'View Staff'),
        ('manage_categories', 'Manage Categories'),
        ('view_categories', 'View Categories'),
        ('manage_tables', 'Manage Tables'),
        ('view_tables', 'View Tables'),
        ('manage_payments', 'Manage Payments'),
        ('view_payments', 'View Payments'),
    ]

    for code, label in predefined_permissions:
        Permission.objects.get_or_create(code=code, label=label)        
        
        
        
# Table status change
@receiver(pre_save, sender=Table)
def log_table_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # skip on creation

    previous = Table.objects.get(pk=instance.pk)

    if previous.status != instance.status:
        msg = f"Table {instance.number} changed to {instance.status}"
        type_map = {
            "available": "success",
            "cleaning": "success",
            "occupied": "warning",
            "reserved": "info"
        }
        UpdateLog.objects.create(message=msg, type=type_map.get(instance.status, "info"))


# Reservation created
@receiver(post_save, sender=Reservation)
def log_new_reservation(sender, instance, created, **kwargs):
    if created:
        msg = f"New reservation for Table {instance.table.number} at {instance.time}"
        UpdateLog.objects.create(message=msg, type="info")


# Order status change
@receiver(pre_save, sender=Order)
def log_order_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    previous = Order.objects.get(pk=instance.pk)
    if previous.status != instance.status and instance.status == "completed":
        msg = f"Table {instance.table.number} order completed - Rs. {instance.total_amount}"
        UpdateLog.objects.create(message=msg, type="info")        
        
        

@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.user,
            icon='utensils',
            title='Order Placed Successfully',
            message=f"Your order #{instance.pk} has been placed successfully.",
        )
  


@receiver(post_save, sender=Order)
def order_delivered_notification(sender, instance, created, **kwargs):
    if not created and instance.status == 'delivered':
        message = f"Your order #{instance.pk} has been delivered."
        # Avoid duplicate notification for the same user
        if not Notification.objects.filter(title="Order Delivered", message=message, user=instance.user).exists():
            Notification.objects.create(
                user=instance.user,
                icon='check_circle',
                title='Order Delivered',
                message=message,
            )