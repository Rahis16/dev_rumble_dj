from django.db import models
from django.contrib.auth.models import User


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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    semester = models.PositiveIntegerField(
        choices=SEMESTER_CHOICES, blank=True, null=True
    )
    faculty = models.CharField(
        max_length=100, choices=FACULTY_CHOICES, blank=True, null=True
    )
    year = models.PositiveIntegerField(choices=YEAR_CHOICES, blank=True, null=True)
    lcid = models.CharField(max_length=50, unique=True, verbose_name="College ID")
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

    def __str__(self):
        return self.user.username


# portfolio
class Portfolio(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="portfolio"
    )
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Portfolio"


# skills
class Skill(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="skills"
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.portfolio.user.username})"


class Interest(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="interests"
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.portfolio.user.username})"


class Project(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="projects"
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    file = models.FileField(upload_to="project_files/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.portfolio.user.username})"


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
