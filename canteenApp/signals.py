from django.db.models.signals import post_save
from django.dispatch import receiver
# from django.contrib.auth.models import User
from django.conf import settings
from .models import UserProfile, Wallet, StaffProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        
        
        
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)        
        
        

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_staff_profile(sender, instance, created, **kwargs):
    if created and instance.is_staff:
        StaffProfile.objects.create(user=instance)
        