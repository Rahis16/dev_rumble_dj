from django.contrib import admin
from .models import *


# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "lcid",
        "faculty",
        "semester",
        "year",
        "contact_number",
        "gender",
        "photo_preview",
    )
    list_filter = ("faculty", "semester", "year", "gender")
    search_fields = ("user__username", "lcid", "faculty", "contact_number")
    readonly_fields = ("photo_preview",)

    fieldsets = (
        (
            "User Info",
            {"fields": ("user", "lcid", "faculty", "semester", "year", "gender")},
        ),
        (
            "Contact Details",
            {"fields": ("contact_number", "temp_address", "perm_address")},
        ),
        ("Education", {"fields": ("school", "college", "background")}),
        ("Profile", {"fields": ("bio", "photo", "photo_preview")}),
    )

    def photo_preview(self, obj):
        if obj.photo:
            return f'<img src="{obj.photo.url}" style="max-height:100px; border-radius:5px;" />'
        return "(No Image)"

    photo_preview.allow_tags = True
    photo_preview.short_description = "Photo Preview"


# portfolio Section
class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1


class InterestInline(admin.TabularInline):
    model = Interest
    extra = 1


class ProjectInline(admin.StackedInline):
    model = Project
    extra = 1
    readonly_fields = ("created_at",)


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("user", "short_bio")
    search_fields = ("user__username", "bio")
    inlines = [SkillInline, InterestInline, ProjectInline]

    def short_bio(self, obj):
        return (obj.bio[:50] + "...") if obj.bio and len(obj.bio) > 50 else obj.bio

    short_bio.short_description = "Bio"


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "portfolio")
    search_fields = ("name", "portfolio__user__username")


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ("name", "portfolio")
    search_fields = ("name", "portfolio__user__username")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "portfolio", "link", "created_at")
    search_fields = ("title", "portfolio__user__username")
    list_filter = ("created_at",)


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("sender__username", "receiver__username")


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 1


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "leader", "created_at")
    search_fields = ("name", "leader__username")
    inlines = [TeamMemberInline]


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "joined_at")
    search_fields = ("user__username", "team__name")
    list_filter = ("joined_at",)


# ------------------ TeamJoinRequest ------------------
@admin.register(TeamJoinRequest)
class TeamJoinRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "status", "created_at")
    search_fields = ("user__username", "team__name")
    list_filter = ("status", "created_at")
    readonly_fields = ("created_at",)


# ------------------ TeamInvitation ------------------
@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ("invited_user", "team", "status", "created_at")
    search_fields = ("invited_user__username", "team__name")
    list_filter = ("status", "created_at")
    readonly_fields = ("created_at",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver_or_team", "short_message", "timestamp")
    search_fields = ("sender__username", "receiver__username", "team__name", "message")
    list_filter = ("timestamp",)

    def receiver_or_team(self, obj):
        return obj.team.name if obj.team else obj.receiver.username

    receiver_or_team.short_description = "Receiver/Team"

    def short_message(self, obj):
        return (obj.message[:50] + "...") if len(obj.message) > 50 else obj.message

    short_message.short_description = "Message"


# Register your models here.
@admin.register(ChatMessageAi)
class ChatMessageAiAdmin(admin.ModelAdmin):
    list_display = ("role", "content", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("content",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
