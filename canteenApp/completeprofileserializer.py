# profiles/serializers.py
from typing import Dict, List
from rest_framework import serializers
from django.db import transaction
from .models import Field, Interest2 as Interest, Skill2 as Skill, UserProfile, UserInterest, UserSkill


class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ["id", "name", "slug"]


class InterestSerializer(serializers.ModelSerializer):
    field = FieldSerializer(read_only=True)

    class Meta:
        model = Interest
        fields = ["id", "name", "field"]


class SkillSerializer(serializers.ModelSerializer):
    field = FieldSerializer(read_only=True)

    class Meta:
        model = Skill
        fields = ["id", "name", "field"]


class UserSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)

    class Meta:
        model = UserSkill
        fields = ["skill", "level"]


class UserSelectionReadSerializer(serializers.Serializer):
    """For GET: return normalized user selection."""

    field = FieldSerializer(allow_null=True)
    interests = InterestSerializer(many=True)
    skills = UserSkillSerializer(many=True)


class UserSelectionWriteSerializer(serializers.Serializer):
    """
    Accepts the exact payload your React sends:

    {
      "field": "IT",
      "interests": ["Web Development", "Cloud Computing"],
      "skills": ["React", "AWS"],
      "skill_level": {"React":"Intermediate","AWS":"Beginner"}
    }
    """

    field = serializers.CharField(allow_blank=False)
    interests: List[str] = serializers.ListField(
        child=serializers.CharField(), allow_empty=False
    )
    skills: List[str] = serializers.ListField(
        child=serializers.CharField(), allow_empty=False
    )
    skill_level: Dict[str, str] = serializers.DictField(child=serializers.CharField())

    def validate(self, attrs):
        # Normalize and basic checks
        attrs["field"] = attrs["field"].strip()
        attrs["interests"] = [i.strip() for i in attrs["interests"] if i.strip()]
        attrs["skills"] = [s.strip() for s in attrs["skills"] if s.strip()]

        # Validate levels (if provided)
        valid_levels = {l for l, _ in UserSkill.SKILL_LEVELS}
        for k, v in attrs.get("skill_level", {}).items():
            if v not in valid_levels:
                raise serializers.ValidationError(
                    {"skill_level": f"Invalid level '{v}' for skill '{k}'."}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        Upsert field, ensure interests/skills belong to that field, then
        replace user's selections with the new ones.
        """
        user = self.context["request"].user
        field_name = validated_data["field"]
        interest_names = validated_data["interests"]
        skill_names = validated_data["skills"]
        skill_levels = validated_data.get("skill_level", {})

        # Field
        field, _ = Field.objects.get_or_create(
            name__iexact=field_name, defaults={"name": field_name}
        )
        if isinstance(field, tuple):  # in case of get_or_create with name__iexact trick
            field = Field.objects.get(name__iexact=field_name)

        # Ensure slug exists (if created via iexact)
        if not field.slug:
            field.save()

        # Interests (tie to field)
        interests = []
        for name in interest_names:
            obj, _ = Interest.objects.get_or_create(
                field=field, name__iexact=name, defaults={"name": name}
            )
            if isinstance(obj, tuple):
                obj = Interest.objects.get(field=field, name__iexact=name)
            interests.append(obj)

        # Skills (tie to field)
        skills = []
        for name in skill_names:
            obj, _ = Skill.objects.get_or_create(
                field=field, name__iexact=name, defaults={"name": name}
            )
            if isinstance(obj, tuple):
                obj = Skill.objects.get(field=field, name__iexact=name)
            skills.append(obj)

        # Save to user profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.selected_field = field
        profile.save()

        # Replace user interests
        UserInterest.objects.filter(user=user).delete()
        UserInterest.objects.bulk_create(
            [UserInterest(user=user, interest=i) for i in interests]
        )

        # Replace user skills
        UserSkill.objects.filter(user=user).delete()
        level_default = UserSkill.BEGINNER
        to_create = []
        for s in skills:
            lvl = skill_levels.get(s.name, level_default)
            to_create.append(UserSkill(user=user, skill=s, level=lvl))
        UserSkill.objects.bulk_create(to_create)

        # Return a normalized representation
        return {
            "field": field,
            "interests": interests,
            "skills": to_create,  # include user levels
        }

    def to_representation(self, instance):
        # Instance is dict returned by create()
        return UserSelectionReadSerializer(instance).data
