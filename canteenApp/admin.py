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
            {"fields": ("user", "full_name", "lcid", "faculty", "semester", "year", "gender")},
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


# youtube video admin ----------------
# videos/admin.py


@admin.register(VideoKeyword)
class VideoKeywordAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(CourseVideo)
class CourseVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "created_at")
    list_filter = ("is_published", "category", "created_at", "fields")
    search_fields = ("title", "description", "youtube_url", "youtube_id")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("fields", "interests", "skills", "keywords")
