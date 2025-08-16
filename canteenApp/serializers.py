from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *
User = get_user_model()


# serializers here
class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    
    class Meta:
        model = UserProfile
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class FriendRequestSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ["id", "sender", "receiver", "status", "created_at"]


class FriendRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ["receiver"]  # Only receiver needed on creatio


class PeerSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    interests = serializers.SerializerMethodField()
    photo = serializers.ImageField(source="userprofile.photo", read_only=True)
    semester = serializers.IntegerField(source="userprofile.semester", read_only=True)
    faculty = serializers.CharField(source="userprofile.faculty", read_only=True)
    year = serializers.IntegerField(source="userprofile.year", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "photo",
            "semester",
            "faculty",
            "year",
            "skills",
            "interests",
        ]

    def get_skills(self, obj):
        if hasattr(obj, "portfolio"):
            return [skill.name for skill in obj.portfolio.skills.all()]
        return []

    def get_interests(self, obj):
        if hasattr(obj, "portfolio"):
            return [interest.name for interest in obj.portfolio.interests.all()]
        return []


class TeamSerializer(serializers.ModelSerializer):
    leader = UserSerializer(read_only=True)
    members = UserSerializer(source="members", many=True, read_only=True)

    class Meta:
        model = Team
        fields = ["id", "name", "description", "leader", "members", "created_at"]


class TeamJoinRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    team = TeamSerializer(read_only=True)

    class Meta:
        model = TeamJoinRequest
        fields = ["id", "team", "user", "status", "created_at"]


class TeamJoinRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamJoinRequest
        fields = ["team"]


class TeamInvitationSerializer(serializers.ModelSerializer):
    invited_user = UserSerializer(read_only=True)
    team = TeamSerializer(read_only=True)

    class Meta:
        model = TeamInvitation
        fields = ["id", "team", "invited_user", "status", "created_at"]


class TeamInvitationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamInvitation
        fields = ["team", "invited_user"]


class TeamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["name", "description"]
