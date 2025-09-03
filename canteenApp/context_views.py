# videos/views_context.py
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import CourseVideo
from .models import VideoContext
from .classroomserializer import VideoContextSerializer, VideoContextWriteSerializer

class VideoContextRetrieveView(APIView):
    """
    GET /api/videos/<slug:slug>/context/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug, *args, **kwargs):
        video = get_object_or_404(CourseVideo, slug=slug, is_published=True)
        ctx = getattr(video, "context", None)
        if not ctx:
            return Response({"detail": "No context yet."}, status=200)
        return Response(VideoContextSerializer(ctx).data)

class VideoContextUpsertView(APIView):
    """
    POST/PUT (admin): create/update a video's context + segments.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, slug, *args, **kwargs):
        video = get_object_or_404(CourseVideo, slug=slug)
        ser = VideoContextWriteSerializer(data=request.data, context={"video": video})
        ser.is_valid(raise_exception=True)
        ctx = ser.save()
        return Response(VideoContextSerializer(ctx).data, status=status.HTTP_201_CREATED)

    def put(self, request, slug, *args, **kwargs):
        return self.post(request, slug, *args, **kwargs)
