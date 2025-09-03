# # profiles/models.py
# from django.conf import settings
# from django.db import models
# from django.utils.text import slugify


# class Field(models.Model):
#     name = models.CharField(max_length=120, unique=True)
#     slug = models.SlugField(max_length=140, unique=True, blank=True)

#     class Meta:
#         ordering = ["name"]

#     def _str_(self):
#         return self.name

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.name)
#         super().save(*args, **kwargs)


# class Interest(models.Model):
#     name = models.CharField(max_length=120)
#     field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name="interests")

#     class Meta:
#         unique_together = ("name", "field")
#         ordering = ["name"]

#     def _str_(self):
#         return f"{self.name} ({self.field.name})"


# class Skill(models.Model):
#     name = models.CharField(max_length=120)
#     field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name="skills")

#     class Meta:
#         unique_together = ("name", "field")
#         ordering = ["name"]

#     def _str_(self):
#         return f"{self.name} ({self.field.name})"


# class UserProfile(models.Model):
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
#     )
#     selected_field = models.ForeignKey(
#         Field, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
#     )

#     def _str_(self):
#         return f"Profile<{self.user}>"


# class UserInterest(models.Model):
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="user_interests",
#     )
#     interest = models.ForeignKey(
#         Interest, on_delete=models.CASCADE, related_name="user_links"
#     )

#     class Meta:
#         unique_together = ("user", "interest")


# class UserSkill(models.Model):
#     BEGINNER = "Beginner"
#     INTERMEDIATE = "Intermediate"
#     ADVANCED = "Advanced"
#     SKILL_LEVELS = [
#         (BEGINNER, "Beginner"),
#         (INTERMEDIATE, "Intermediate"),
#         (ADVANCED, "Advanced"),
#     ]

#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_skills"
#     )
#     skill = models.ForeignKey(
#         Skill, on_delete=models.CASCADE, related_name="user_links"
#     )
#     level = models.CharField(max_length=20, choices=SKILL_LEVELS, default=BEGINNER)

#     class Meta:
#         unique_together = ("user", "skill")
