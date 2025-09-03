# profiles/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Field, Interest2 as Interest, Skill2 as Skill
from .models import UserInterest, UserProfile, UserInterest, UserSkill
from .completeprofileserializer import (
    FieldSerializer,
    InterestSerializer,
    SkillSerializer,
    UserSelectionWriteSerializer,
    UserSelectionReadSerializer,
)


class IsAuthenticated(permissions.IsAuthenticated):
    pass


# --- Catalog Endpoints ---


class FieldListView(generics.ListAPIView):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    permission_classes = [permissions.AllowAny]


class InterestListByFieldView(generics.ListAPIView):
    serializer_class = InterestSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        /api/catalog/interests/?field=IT  (by name)
        /api/catalog/interests/?field_id=3 (by id)
        """
        qs = Interest.objects.select_related("field").all()
        field_name = self.request.query_params.get("field")
        field_id = self.request.query_params.get("field_id")
        if field_id:
            return qs.filter(field_id=field_id)
        if field_name:
            return qs.filter(field__name__iexact=field_name)
        return qs.none()  # require filter


class SkillListByFieldView(generics.ListAPIView):
    serializer_class = SkillSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        /api/catalog/skills/?field=IT
        /api/catalog/skills/?field_id=3
        """
        qs = Skill.objects.select_related("field").all()
        field_name = self.request.query_params.get("field")
        field_id = self.request.query_params.get("field_id")
        if field_id:
            return qs.filter(field_id=field_id)
        if field_name:
            return qs.filter(field__name__iexact=field_name)
        return qs.none()


# --- Save & Fetch User Selection ---


class SaveSkillsInterestsView(APIView):
    """
    POST /api/save-skills-interests/
    Body:
    {
      "field": "IT",
      "interests": ["Web Development", "Cloud Computing"],
      "skills": ["React", "AWS"],
      "skill_level": {"React":"Intermediate","AWS":"Beginner"}
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = UserSelectionWriteSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.save()  # returns normalized selection
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GetMySelectionView(APIView):
    """
    GET /api/my-selection/
    Returns the saved selection for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        field = profile.selected_field

        interests = (
            Interest.objects.filter(user_links__user=user)
            .select_related("field")
            .order_by("name")
        )

        skills = (
            UserSkill.objects.filter(user=user)
            .select_related("skill__field")
            .order_by("skill__name")
        )

        payload = {
            "field": field,
            "interests": list(interests),
            "skills": list(skills),  # contains levels
        }
        return Response(UserSelectionReadSerializer(payload).data)
