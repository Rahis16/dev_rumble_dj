# videos/views_classroom.py
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Classroom, ClassroomItem, VideoContext
from .models import CourseVideo
from .classroomserializer import (
    ClassroomSerializer,
    ClassroomItemSerializer,
    VideoContextSerializer,
    VideoContextWriteSerializer,
)

def get_user_classroom(user):
    cls, _ = Classroom.objects.get_or_create(user=user, defaults={"name": "My AI Classroom"})
    return cls

# --- One classroom per user ---

class ClassroomMeView(APIView):
    """
    GET /api/classroom/  → retrieve (auto-create)
    PATCH /api/classroom/ → rename / set active_video_id
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        cls = get_user_classroom(request.user)
        return Response(ClassroomSerializer(cls).data)

    def patch(self, request, *args, **kwargs):
        cls = get_user_classroom(request.user)
        serializer = ClassroomSerializer(cls, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# --- Items (no classroom_id in URL now) ---

class ClassroomItemAddView(APIView):
    """
    POST /api/classroom/items/
    { "video_id": 123, "note": "" } → idempotent
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cls = get_user_classroom(request.user)
        video = get_object_or_404(CourseVideo, pk=request.data.get("video_id"), is_published=True)
        note = request.data.get("note", "")
        item, created = ClassroomItem.objects.get_or_create(
            classroom=cls, video=video, defaults={"note": note}
        )
        if not created and note and note != item.note:
            item.note = note
            item.save(update_fields=["note"])
        return Response(ClassroomItemSerializer(item).data, status=status.HTTP_201_CREATED)

class ClassroomItemListView(generics.ListAPIView):
    """
    GET /api/classroom/items/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClassroomItemSerializer

    def get_queryset(self):
        cls = get_user_classroom(self.request.user)
        return ClassroomItem.objects.filter(classroom=cls).select_related("video")

class ClassroomItemDeleteView(APIView):
    """
    DELETE /api/classroom/items/<int:item_id>/
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, item_id, *args, **kwargs):
        cls = get_user_classroom(request.user)
        item = get_object_or_404(ClassroomItem, pk=item_id, classroom=cls)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ClassroomSetActiveVideoView(APIView):
    """
    POST /api/classroom/set-active/
    { "video_id": 123 }  # ensures it's in the classroom
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cls = get_user_classroom(request.user)
        vid = get_object_or_404(CourseVideo, pk=request.data.get("video_id"), is_published=True)
        ClassroomItem.objects.get_or_create(classroom=cls, video=vid)
        cls.active_video = vid
        cls.save(update_fields=["active_video"])
        return Response(ClassroomSerializer(cls).data)

class ClassroomItemProgressView(APIView):
    """
    PATCH /api/classroom/items/<int:item_id>/progress/
    { "progress_seconds": 480, "completed": false }
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, item_id, *args, **kwargs):
        cls = get_user_classroom(request.user)
        item = get_object_or_404(ClassroomItem, pk=item_id, classroom=cls)
        progress = request.data.get("progress_seconds")
        completed = request.data.get("completed")
        changed = False
        if isinstance(progress, int) and progress >= 0:
            item.progress_seconds = progress
            item.last_watched_at = timezone.now()
            changed = True
        if completed is not None:
            item.completed = bool(completed)
            changed = True
        if changed:
            item.save(update_fields=["progress_seconds", "completed", "last_watched_at"])
        return Response(ClassroomItemSerializer(item).data)
