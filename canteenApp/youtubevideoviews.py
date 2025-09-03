# videos/views.py
from django.db.models import Count, Q, IntegerField, F
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models

from .models import CourseVideo, VideoKeyword
from .youtubevideoserializer import (
    CourseVideoSerializer,
    CourseVideoWriteSerializer,
)
from .models import UserInterest, UserSkill

# --- CRUD / Catalog ---


class CourseVideoListCreateView(generics.ListCreateAPIView):
    """
    GET: list (with filters)
    POST: create (admin/staff or authenticated as you prefer)
    Filters:
      ?q=react&category=Frontend&keyword=hooks&is_published=true
    """

    queryset = CourseVideo.objects.filter(is_published=True).prefetch_related(
        "fields", "interests", "skills", "keywords"
    )
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CourseVideoWriteSerializer
        return CourseVideoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("q")
        category = self.request.query_params.get("category")
        keyword = self.request.query_params.get("keyword")
        published = self.request.query_params.get("is_published")

        if q:
            qs = qs.filter(Q(title_icontains=q) | Q(description_icontains=q))
        if category:
            qs = qs.filter(category__iexact=category)
        if keyword:
            qs = qs.filter(keywords_name_iexact=keyword)
        if published in ("true", "false"):
            qs = qs.filter(is_published=(published == "true"))

        return qs.distinct()


class CourseVideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CourseVideo.objects.all().prefetch_related(
        "fields", "interests", "skills", "keywords"
    )
    lookup_field = "slug"  # or 'pk'
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return CourseVideoWriteSerializer
        return CourseVideoSerializer


# --- Recommendations ---


# class RecommendedVideosView(APIView):
#     """
#     GET /api/videos/recommended/
#     Optional filters: ?limit=12&category=Frontend&q=react
#     Strategy:
#       - Collect user’s interest names, skill names, and their fields
#       - Match CourseVideo by:
#           * same fields / interests / skills (M2M)
#           * OR keyword overlap with (interest/skill names)
#       - Score = #field_matches + #interest_matches + #skill_matches + #keyword_matches
#       - Order by score desc then newest
#     """

#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         user = request.user
#         limit = int(self.request.query_params.get("limit", "12"))
#         q = self.request.query_params.get("q")
#         category = self.request.query_params.get("category")

#         # User signals
#         interest_names = list(
#             UserInterest.objects.filter(user=user)
#             .select_related("interest__field")
#             .values_list("interest__name", flat=True)
#         )
#         skill_names = list(
#             UserSkill.objects.filter(user=user)
#             .select_related("skill__field")
#             .values_list("skill__name", flat=True)
#         )
#         field_ids_from_interests = list(
#             UserInterest.objects.filter(user=user).values_list(
#                 "interest__field_id", flat=True
#             )
#         )
#         field_ids_from_skills = list(
#             UserSkill.objects.filter(user=user).values_list(
#                 "skill__field_id", flat=True
#             )
#         )
#         target_field_ids = set(field_ids_from_interests) | set(field_ids_from_skills)

#         qs = CourseVideo.objects.filter(is_published=True).prefetch_related(
#             "fields", "interests", "skills", "keywords"
#         )

#         # Apply optional UI filters
#         if q:
#             qs = qs.filter(Q(title_icontains=q) | Q(description_icontains=q))
#         if category:
#             qs = qs.filter(category__iexact=category)

#         # Matching conditions
#         cond = (
#             Q(fields_id_in=target_field_ids)
#             | Q(interests_name_in=interest_names)
#             | Q(skills_name_in=skill_names)
#             | Q(keywords_name_in=(interest_names + skill_names))
#         )

#         qs = qs.filter(cond).distinct()

#         # Score by overlap counts
#         qs = (
#             qs.annotate(
#                 field_hits=Count("fields", filter=Q(fields_id_in=target_field_ids)),
#                 interest_hits=Count(
#                     "interests", filter=Q(interests_name_in=interest_names)
#                 ),
#                 skill_hits=Count("skills", filter=Q(skills_name_in=skill_names)),
#                 keyword_hits=Count(
#                     "keywords",
#                     filter=Q(keywords_name_in=(interest_names + skill_names)),
#                 ),
#             )
#             .annotate(
#                 score=Coalesce(
#                     Count(
#                         "id",
#                         filter=Q(
#                             pk__in=models.Subquery(
#                                 CourseVideo.objects.filter(
#                                     pk=models.OuterRef("pk")
#                                 ).values("pk")
#                             )
#                         ),
#                         output_field=IntegerField(),
#                     ),
#                     0,
#                 )
#                 + Coalesce(models.F("field_hits"), 0)
#                 + Coalesce(models.F("interest_hits"), 0)
#                 + Coalesce(models.F("skill_hits"), 0)
#                 + Coalesce(models.F("keyword_hits"), 0)
#             )
#             .order_by("-score", "-created_at")[:limit]
#         )

#         data = CourseVideoSerializer(qs, many=True).data
#         return Response({"count": len(data), "results": data})


class RecommendedVideosView(APIView):
    """
    GET /api/videos/recommended/?limit=12&category=Frontend&q=react
    Matches by user's fields, interests, skills, and keywords (names),
    then orders by overlap score desc, then newest.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        limit = int(request.query_params.get("limit", "12"))
        q = request.query_params.get("q")
        category = request.query_params.get("category")

        # Pull user's signals
        interest_names = list(
            UserInterest.objects.filter(user=user).values_list("interest__name", flat=True)
        )
        skill_names = list(
            UserSkill.objects.filter(user=user).values_list("skill__name", flat=True)
        )
        field_ids_from_interests = list(
            UserInterest.objects.filter(user=user).values_list("interest__field_id", flat=True)
        )
        field_ids_from_skills = list(
            UserSkill.objects.filter(user=user).values_list("skill__field_id", flat=True)
        )
        target_field_ids = list(set(field_ids_from_interests) | set(field_ids_from_skills))

        qs = CourseVideo.objects.filter(is_published=True).prefetch_related(
            "fields", "interests", "skills", "keywords"
        )

        # Optional UI filters
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if category:
            qs = qs.filter(category__iexact=category)

        # If user has no signals and no text/category filters, short-circuit to empty
        if not (interest_names or skill_names or target_field_ids):
            return Response({"count": 0, "results": []})

        # Matching condition (correct lookups)
        cond = (
            Q(fields__id__in=target_field_ids) |
            Q(interests__name__in=interest_names) |
            Q(skills__name__in=skill_names) |
            Q(keywords__name__in=(interest_names + skill_names))
        )
        qs = qs.filter(cond).distinct()

        # Score overlaps (use distinct to avoid overcount due to M2M joins)
        qs = qs.annotate(
            field_hits=Count("fields", filter=Q(fields__id__in=target_field_ids), distinct=True),
            interest_hits=Count("interests", filter=Q(interests__name__in=interest_names), distinct=True),
            skill_hits=Count("skills", filter=Q(skills__name__in=skill_names), distinct=True),
            keyword_hits=Count("keywords", filter=Q(keywords__name__in=(interest_names + skill_names)), distinct=True),
        ).annotate(
            score=Coalesce(F("field_hits"), 0)
                + Coalesce(F("interest_hits"), 0)
                + Coalesce(F("skill_hits"), 0)
                + Coalesce(F("keyword_hits"), 0)
        ).order_by("-score", "-created_at")[:limit]

        data = CourseVideoSerializer(qs, many=True).data
        return Response({"count": len(data), "results": data})