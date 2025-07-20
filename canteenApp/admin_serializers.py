# admin_serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Role, Permission, UserProfile
from django.contrib.auth import get_user_model
from .admin_role_serializers import UserStatusSerializer



class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username']


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['code', 'label']
        
        
class PermissionSerializerAddRoleView(serializers.ModelSerializer): #for adding permission on listcreaterole
    class Meta:
        model = Permission
        fields = ['id', 'code', 'label']        


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(
        many=True, slug_field='code', queryset=Permission.objects.all()
    )
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions', 'description', 'created_at', 'user_count']

    def get_user_count(self, obj):
        return obj.users.count()
    

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    role = serializers.SlugRelatedField(slug_field='name', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', format='%Y-%m-%dT%H:%M:%SZ')
    user = UserStatusSerializer(read_only=True)


    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email', 'role', 'status',
            'created_at', 'last_login', 'phone_number', 'profile_pic',
            'orders_count', 'total_spent', 'user'
        ]


class RoleSerializerCreateView(serializers.ModelSerializer):  #for creating roles
    permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all()
    )
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'created_at']

    def create(self, validated_data):
        permissions = validated_data.pop('permissions', [])
        role = Role.objects.create(**validated_data)
        role.permissions.set(permissions)
        return role