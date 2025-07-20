# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Role, Permission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['code', 'label']

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True)

    class Meta:
        model = Role
        fields = ['name', 'description', 'permissions']

class UserProfileSerializer(serializers.ModelSerializer):
    role = RoleSerializer()

    class Meta:
        model = UserProfile
        fields = [
            'full_name', 'status', 'profile_pic', 'role',
            'faculty', 'section', 'program', 'semester',
        ]

class UserStatusSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['username', 'email', 'is_staff', 'is_superuser', 'is_active', 'profile']
