from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings


class Field(models.Model):
    name = models.CharField(max_length=120, unique=True , default="IT")
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def _str_(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    # Choice options
    FACULTY_CHOICES = [
        ("BSc.CSIT", "BSc. CSIT"),
        ("BIT", "Bachelor of Information Technology"),
        ("BBA", "Bachelor of Business Administration"),
        ("BBS", "Bachelor of Business Studies"),
        ("B.Ed", "Bachelor of Education"),
        ("BSc", "Bachelor of Science"),
        ("BA", "Bachelor of Arts"),
    ]

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    SEMESTER_CHOICES = [(i, f"Semester {i}") for i in range(1, 9)]
    YEAR_CHOICES = [(i, f"Year {i}") for i in range(1, 5)]

    # Fields
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    semester = models.PositiveIntegerField(
        choices=SEMESTER_CHOICES, blank=True, null=True
    )
    faculty = models.CharField(
        max_length=100, choices=FACULTY_CHOICES, blank=True, null=True
    )
    year = models.PositiveIntegerField(choices=YEAR_CHOICES, blank=True, null=True)
    lcid = models.CharField(max_length=50, unique=True, verbose_name="College ID", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    temp_address = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Temporary Address"
    )
    perm_address = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Permanent Address"
    )
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, blank=True, null=True
    )
    school = models.CharField(max_length=100, blank=True, null=True)
    college = models.CharField(max_length=100, blank=True, null=True)
    background = models.TextField(blank=True, null=True)
    selected_field = models.ForeignKey(
        Field, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )

    def __str__(self):
        return self.user.username


class Interest2(models.Model):
    name = models.CharField(max_length=120)
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name="interests")

    class Meta:
        unique_together = ("name", "field")
        ordering = ["name"]

    def _str_(self):
        return f"{self.name} ({self.field.name})"


class Skill2(models.Model):
    name = models.CharField(max_length=120)
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name="skills")

    class Meta:
        unique_together = ("name", "field")
        ordering = ["name"]

    def _str_(self):
        return f"{self.name} ({self.field.name})"


# class UserProfile(models.Model):
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
#     )
#     selected_field = models.ForeignKey(
#         Field, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
#     )

#     def _str_(self):
#         return f"Profile<{self.user}>"


class UserInterest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_interests",
    )
    interest = models.ForeignKey(
        Interest2, on_delete=models.CASCADE, related_name="user_links"
    )

    class Meta:
        unique_together = ("user", "interest")


class UserSkill(models.Model):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    SKILL_LEVELS = [
        (BEGINNER, "Beginner"),
        (INTERMEDIATE, "Intermediate"),
        (ADVANCED, "Advanced"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_skills"
    )
    skill = models.ForeignKey(
        Skill2, on_delete=models.CASCADE, related_name="user_links"
    )
    level = models.CharField(max_length=20, choices=SKILL_LEVELS, default=BEGINNER)

    class Meta:
        unique_together = ("user", "skill")


# completet profile model completed here---------------------------------------


# peer finder section
class FriendRequest(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_requests"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_requests"
    )
    status = models.CharField(
        max_length=10,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("sender", "receiver")

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.status})"


# group section
class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name="led_teams")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Restricts to one team
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} in {self.team.name}"


class TeamJoinRequest(models.Model):
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="join_requests"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="team_join_requests"
    )
    status = models.CharField(
        max_length=10,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("team", "user")  # Prevent duplicate requests

    def __str__(self):
        return f"{self.user.username} -> {self.team.name} ({self.status})"


class TeamInvitation(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="invitations")
    invited_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="team_invitations"
    )
    status = models.CharField(
        max_length=10,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("team", "invited_user")  # Prevent duplicate invites

    def __str__(self):
        return (
            f"{self.invited_user.username} invited to {self.team.name} ({self.status})"
        )


# chat and file sharing
class ChatMessage(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_messages",
        null=True,
        blank=True,
    )
    team = models.ForeignKey(
        "Team", on_delete=models.CASCADE, null=True, blank=True
    )  # If team chat
    message = models.TextField()
    file = models.FileField(upload_to="chat_files/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.team:
            return f"Team Chat ({self.team.name}) - {self.sender.username}"
        return f"Private Chat - {self.sender.username} → {self.receiver.username}"


class ChatMessageAi(models.Model):
    role = models.CharField(max_length=20)  # 'system', 'user', 'assistant'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
