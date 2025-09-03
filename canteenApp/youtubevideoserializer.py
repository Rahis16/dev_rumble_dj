# videos/serializers.py
from rest_framework import serializers
from .models import CourseVideo, VideoKeyword
from .models import Field, Interest2, Skill2


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoKeyword
        fields = ["id", "name"]


class FieldMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ["id", "name", "slug"]


class InterestMiniSerializer(serializers.ModelSerializer):
    field = FieldMiniSerializer(read_only=True)

    class Meta:
        model = Interest2
        fields = ["id", "name", "field"]


class SkillMiniSerializer(serializers.ModelSerializer):
    field = FieldMiniSerializer(read_only=True)

    class Meta:
        model = Skill2
        fields = ["id", "name", "field"]


class CourseVideoSerializer(serializers.ModelSerializer):
    keywords = KeywordSerializer(many=True, read_only=True)
    fields = FieldMiniSerializer(many=True, read_only=True)
    interests = InterestMiniSerializer(many=True, read_only=True)
    skills = SkillMiniSerializer(many=True, read_only=True)

    class Meta:
        model = CourseVideo
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "category",
            "youtube_url",
            "youtube_id",
            "keywords",
            "fields",
            "interests",
            "skills",
            "created_at",
            "is_published",
        ]


class CourseVideoWriteSerializer(serializers.ModelSerializer):
    """
    Accepts either IDs for M2M or keyword names for quick creation.
    {
      "title": "...",
      "description": "...",
      "category": "Frontend",
      "youtube_url": "https://youtube.com/watch?v=...",
      "field_ids": [1,2],
      "interest_ids": [10,22],
      "skill_ids": [5,7],
      "keywords": ["react", "hooks", "frontend"]
    }
    """

    field_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    interest_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    skill_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    keywords = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = CourseVideo
        fields = [
            "title",
            "description",
            "category",
            "youtube_url",
            "is_published",
            "field_ids",
            "interest_ids",
            "skill_ids",
            "keywords",
        ]

    def create(self, validated):
        fields_ids = validated.pop("field_ids", [])
        interests_ids = validated.pop("interest_ids", [])
        skills_ids = validated.pop("skill_ids", [])
        keywords = [k.strip() for k in validated.pop("keywords", []) if k.strip()]

        video = CourseVideo.objects.create(**validated)

        if fields_ids:
            video.fields.set(Field.objects.filter(id__in=fields_ids))
        if interests_ids:
            video.interests.set(Interest2.objects.filter(id__in=interests_ids))
        if skills_ids:
            video.skills.set(Skill2.objects.filter(id__in=skills_ids))
        if keywords:
            from .models import VideoKeyword

            kw_objs = []
            for k in keywords:
                obj, _ = VideoKeyword.objects.get_or_create(
                    name__iexact=k, defaults={"name": k}
                )
                if isinstance(obj, tuple):  # safety if using this pattern elsewhere
                    obj = VideoKeyword.objects.get(name__iexact=k)
                kw_objs.append(obj)
            video.keywords.set(kw_objs)

        return video

    def update(self, instance, validated):
        fields_ids = validated.pop("field_ids", None)
        interests_ids = validated.pop("interest_ids", None)
        skills_ids = validated.pop("skill_ids", None)
        keywords = validated.pop("keywords", None)

        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()

        if fields_ids is not None:
            instance.fields.set(Field.objects.filter(id__in=fields_ids))
        if interests_ids is not None:
            instance.interests.set(Interest2.objects.filter(id__in=interests_ids))
        if skills_ids is not None:
            instance.skills.set(Skill2.objects.filter(id__in=skills_ids))
        if keywords is not None:
            kw_objs = []
            for k in [x.strip() for x in keywords if x.strip()]:
                obj, _ = VideoKeyword.objects.get_or_create(
                    name__iexact=k, defaults={"name": k}
                )
                if isinstance(obj, tuple):
                    obj = VideoKeyword.objects.get(name__iexact=k)
                kw_objs.append(obj)
            instance.keywords.set(kw_objs)

        return instance
