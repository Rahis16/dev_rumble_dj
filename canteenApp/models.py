from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings
from urllib.parse import urlparse, parse_qs


class Field(models.Model):
    name = models.CharField(max_length=120, unique=True , default="IT")
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
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

    def __str__(self):
        return f"{self.name} ({self.field.name})"


class Skill2(models.Model):
    name = models.CharField(max_length=120)
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name="skills")

    class Meta:
        unique_together = ("name", "field")
        ordering = ["name"]

    def __str__(self):
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


class VideoKeyword(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CourseVideo(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80, db_index=True)
    youtube_url = models.URLField()
    youtube_id = models.CharField(max_length=32, blank=True, db_index=True)

    # Link to your profile taxonomy for accurate matching
    fields = models.ManyToManyField(Field, blank=True, related_name="course_videos")
    interests = models.ManyToManyField(
        Interest2, blank=True, related_name="course_videos"
    )
    skills = models.ManyToManyField(Skill2, blank=True, related_name="course_videos")

    # Generic keywords to catch free-form matches (title/desc synonyms, etc.)
    keywords = models.ManyToManyField(VideoKeyword, blank=True, related_name="videos")
    
    #note of the video
    notes = models.TextField(blank=True, default="Video Note!")

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["youtube_id"]),
        ]

    def __str__(self):
        return self.title

    def extract_youtube_id(self) -> str:
        """
        Supports:
        - https://youtu.be/VIDEOID
        - https://www.youtube.com/watch?v=VIDEOID
        - https://www.youtube.com/embed/VIDEOID
        - https://www.youtube.com/shorts/VIDEOID
        Falls back to last path segment if no v query.
        """
        try:
            u = urlparse(self.youtube_url)
            host = (u.hostname or "").lower()
            if host == "youtu.be":
                return (u.path or "/").strip("/")

            if "youtube.com" in host:
                qs_v = parse_qs(u.query).get("v", [None])[0]
                if qs_v:
                    return qs_v
                parts = [p for p in (u.path or "").split("/") if p]
                for tag in ("embed", "shorts"):
                    if tag in parts:
                        i = parts.index(tag)
                        if i + 1 < len(parts):
                            return parts[i + 1]
                if parts:
                    return parts[-1]
        except Exception:
            pass
        return ""  # store blank if unknown

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:240]
        # keep youtube_id in sync
        self.youtube_id = self.extract_youtube_id()
        super().save(*args, **kwargs)


# youtube video model ended-------------------------------------------------


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



# classroom models
# videos/models_classroom.py

class Classroom(models.Model):
    """
    Exactly one classroom per user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="classroom",
    )
    name = models.CharField(max_length=120, default="My AI Classroom")
    active_video = models.ForeignKey(
        CourseVideo, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.name}"


class ClassroomItem(models.Model):
    """
    Videos saved into the user's single classroom.
    """
    classroom = models.ForeignKey(
        Classroom, on_delete=models.CASCADE, related_name="items"
    )
    video = models.ForeignKey(
        CourseVideo, on_delete=models.CASCADE, related_name="classroom_items"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    # Optional learning state
    note = models.TextField(default="Video Note!")
    progress_seconds = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    last_watched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("classroom", "video")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.classroom} → {self.video}"


class VideoContext(models.Model):
    """
    One context per video (time-coded outline).
    """
    video = models.OneToOneField(
        CourseVideo, on_delete=models.CASCADE, related_name="context"
    )
    summary = models.TextField(blank=True, default="")
    keywords = models.JSONField(blank=True, default=list)

    def __str__(self):
        return f"Context for {self.video.title}"


class VideoContextSegment(models.Model):
    context = models.ForeignKey(
        VideoContext, on_delete=models.CASCADE, related_name="segments"
    )
    start_seconds = models.PositiveIntegerField()
    end_seconds = models.PositiveIntegerField()
    title = models.CharField(max_length=200, blank=True, default="")
    content = models.TextField()
    tags = models.JSONField(blank=True, default=list)

    class Meta:
        ordering = ["start_seconds"]

    def __str__(self):
        return f"{self.context.video.title} [{self.start_seconds}-{self.end_seconds}]"
