from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import *
from .serializers import *
from rest_framework.views import APIView

User = get_user_model()

def home(request):
    return HttpResponse("<h1>This is Backend for Dev Rumble made in Django!</h1>")


# ------------------ List & Send Friend Requests ------------------
class FriendRequestListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Show friend requests where user is sender or receiver
        return FriendRequest.objects.filter(
            sender=self.request.user
        ) | FriendRequest.objects.filter(receiver=self.request.user)

    def post(self, request, *args, **kwargs):
        serializer = FriendRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receiver = serializer.validated_data["receiver"]

        if receiver == request.user:
            return Response(
                {"error": "You cannot send request to yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent duplicate requests
        if FriendRequest.objects.filter(
            sender=request.user, receiver=receiver
        ).exists():
            return Response(
                {"error": "Friend request already sent."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        friend_request = FriendRequest.objects.create(
            sender=request.user, receiver=receiver
        )
        return Response(
            FriendRequestSerializer(friend_request).data, status=status.HTTP_201_CREATED
        )


# ------------------ Accept / Reject / View Single Friend Request ------------------
class FriendRequestRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        friend_request = self.get_object()
        if friend_request.receiver != request.user:
            return Response(
                {"error": "You can only accept/reject requests sent to you."},
                status=status.HTTP_403_FORBIDDEN,
            )

        status_update = request.data.get("status")
        if status_update not in ["accepted", "rejected"]:
            return Response(
                {"error": "Status must be 'accepted' or 'rejected'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        friend_request.status = status_update
        friend_request.save()
        return Response(FriendRequestSerializer(friend_request).data)


class PeerRecommendationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, "portfolio"):
            return Response({"error": "You do not have a portfolio yet."}, status=400)

        user_skills = set(skill.name.lower() for skill in user.portfolio.skills.all())
        user_interests = set(
            interest.name.lower() for interest in user.portfolio.interests.all()
        )

        # Exclude the current user
        all_users = User.objects.exclude(id=user.id).filter(portfolio__isnull=False)
        recommendations = []

        for u in all_users:
            u_skills = set(skill.name.lower() for skill in u.portfolio.skills.all())
            u_interests = set(
                interest.name.lower() for interest in u.portfolio.interests.all()
            )

            # Matching score (simple overlap count)
            score = len(user_skills & u_skills) + len(user_interests & u_interests)
            if score > 0:
                recommendations.append((score, u))

        # Sort by score descending
        recommendations.sort(key=lambda x: x[0], reverse=True)

        # Return top 10 recommendations
        top_users = [user for score, user in recommendations[:10]]
        serializer = PeerSerializer(top_users, many=True)
        return Response(serializer.data)


# ------------------ List all teams ------------------
class TeamListAPIView(generics.ListAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]


# ------------------ Join Request ------------------
class TeamJoinRequestAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Show requests made by this user
        return TeamJoinRequest.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TeamJoinRequestCreateSerializer
        return TeamJoinRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = TeamJoinRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.validated_data["team"]

        if TeamMember.objects.filter(user=request.user).exists():
            return Response({"error": "You are already in a team."}, status=400)

        if TeamJoinRequest.objects.filter(
            team=team, user=request.user, status="pending"
        ).exists():
            return Response({"error": "Join request already sent."}, status=400)

        join_request = TeamJoinRequest.objects.create(team=team, user=request.user)
        return Response(TeamJoinRequestSerializer(join_request).data, status=201)


# ------------------ Invitations ------------------
class TeamInvitationAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Invitations for the current user
        return TeamInvitation.objects.filter(invited_user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TeamInvitationCreateSerializer
        return TeamInvitationSerializer

    def post(self, request, *args, **kwargs):
        serializer = TeamInvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.validated_data["team"]
        invited_user = serializer.validated_data["invited_user"]

        if team.leader != request.user:
            return Response({"error": "Only leader can invite users."}, status=403)

        if TeamMember.objects.filter(user=invited_user).exists():
            return Response({"error": "User is already in a team."}, status=400)

        if TeamInvitation.objects.filter(
            team=team, invited_user=invited_user, status="pending"
        ).exists():
            return Response({"error": "Invitation already sent."}, status=400)

        invitation = TeamInvitation.objects.create(team=team, invited_user=invited_user)
        return Response(TeamInvitationSerializer(invitation).data, status=201)


# ------------------ Accept / Reject Invitation ------------------
class TeamInvitationUpdateAPIView(generics.UpdateAPIView):
    queryset = TeamInvitation.objects.all()
    serializer_class = TeamInvitationSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        invitation = self.get_object()
        if invitation.invited_user != request.user:
            return Response(
                {"error": "You can only accept/reject your own invitations."},
                status=403,
            )

        status_update = request.data.get("status")
        if status_update not in ["accepted", "rejected"]:
            return Response(
                {"error": "Status must be 'accepted' or 'rejected'."}, status=400
            )

        if status_update == "accepted":
            if TeamMember.objects.filter(user=request.user).exists():
                return Response({"error": "You are already in a team."}, status=400)
            TeamMember.objects.create(team=invitation.team, user=request.user)

        invitation.status = status_update
        invitation.save()
        return Response(TeamInvitationSerializer(invitation).data)


# ------------------ Leave Team ------------------
class LeaveTeamAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "user_id"

    def get_object(self):
        user = self.request.user
        try:
            return TeamMember.objects.get(user=user)
        except TeamMember.DoesNotExist:
            return None

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj:
            return Response({"error": "You are not in any team."}, status=400)
        obj.delete()
        return Response({"success": "You have left the team."}, status=204)


# ------------------ Create Team ------------------
class TeamCreateAPIView(generics.CreateAPIView):
    serializer_class = TeamCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Only allow creating if user is not already a team leader or member
        if (
            TeamMember.objects.filter(user=self.request.user).exists()
            or Team.objects.filter(leader=self.request.user).exists()
        ):
            raise serializers.ValidationError(
                "You are already in a team or leading a team."
            )
        serializer.save(leader=self.request.user)


# ------------------ Delete Team ------------------
class TeamDeleteAPIView(generics.DestroyAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def delete(self, request, *args, **kwargs):
        team = self.get_object()
        if team.leader != request.user:
            return Response(
                {"error": "Only the team leader can delete the team."},
                status=status.HTTP_403_FORBIDDEN,
            )
        team.delete()
        return Response(
            {"success": "Team deleted successfully."}, status=status.HTTP_204_NO_CONTENT
        )
