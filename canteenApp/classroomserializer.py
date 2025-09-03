# videos/serializers_classroom.py
from rest_framework import serializers
from .models import Classroom, ClassroomItem, VideoContext, VideoContextSegment
from .models import CourseVideo
from .youtubevideoserializer import CourseVideoSerializer  # or a mini version

class CourseVideoMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseVideo
        fields = ("id", "title", "slug", "category", "youtube_url", "youtube_id")

class ClassroomItemSerializer(serializers.ModelSerializer):
    video = CourseVideoMiniSerializer(read_only=True)
    video_id = serializers.PrimaryKeyRelatedField(
        queryset=CourseVideo.objects.filter(is_published=True),
        source="video",
        write_only=True,
    )

    class Meta:
        model = ClassroomItem
        fields = (
            "id",
            "video",
            "video_id",
            "added_at",
            "note",
            "progress_seconds",
            "completed",
            "last_watched_at",
        )

class ClassroomSerializer(serializers.ModelSerializer):
    items = ClassroomItemSerializer(many=True, read_only=True)
    active_video = CourseVideoMiniSerializer(read_only=True)
    active_video_id = serializers.PrimaryKeyRelatedField(
        queryset=CourseVideo.objects.filter(is_published=True),
        source="active_video",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Classroom
        fields = ("id", "name", "active_video", "active_video_id", "created_at", "items")

class VideoContextSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoContextSegment
        fields = ("id", "start_seconds", "end_seconds", "title", "content", "tags")

class VideoContextSerializer(serializers.ModelSerializer):
    segments = VideoContextSegmentSerializer(many=True, read_only=True)

    class Meta:
        model = VideoContext
        fields = ("id", "summary", "keywords", "segments")

class VideoContextWriteSerializer(serializers.ModelSerializer):
    segments = VideoContextSegmentSerializer(many=True)

    class Meta:
        model = VideoContext
        fields = ("summary", "keywords", "segments")

    def create(self, validated_data):
        segs = validated_data.pop("segments", [])
        video = self.context["video"]
        ctx, created = VideoContext.objects.get_or_create(video=video, defaults=validated_data)
        if not created:
            for k, v in validated_data.items():
                setattr(ctx, k, v)
            ctx.save()
        ctx.segments.all().delete()
        for s in segs:
            VideoContextSegment.objects.create(context=ctx, **s)
        return ctx

    def update(self, instance, validated_data):
        segs = validated_data.pop("segments", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if segs is not None:
            instance.segments.all().delete()
            for s in segs:
                VideoContextSegment.objects.create(context=instance, **s)
        return instance
