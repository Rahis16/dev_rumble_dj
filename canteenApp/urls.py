from django.urls import path, include
from . import views
from .import auth_views
from .auth_views import CookieLoginView, CookieLogoutView
from . import Oauth2_views
from . import github_auth_views
from .views import *
from .ai_views import transcribe_and_reply_2
from .completeprofileviews import (
    FieldListView,
    InterestListByFieldView,
    SkillListByFieldView,
    SaveSkillsInterestsView,
    GetMySelectionView,
)

from .youtubevideoviews import (
    CourseVideoListCreateView,
    CourseVideoDetailView,
    RecommendedVideosView,
)


urlpatterns = [
    path("", views.home, name="home"),
    # drf jwt auth urls
    path("auth/login/", CookieLoginView.as_view(), name="rest_login"),
    path("auth/logout/", CookieLogoutView.as_view(), name="rest_logout"),
    path("auth/", include("dj_rest_auth.registration.urls")),  # Signup
    path("auth/status/", auth_views.AuthStatusView.as_view(), name="auth-status"),
    path("token/refresh/", auth_views.RefreshTokenView.as_view(), name="token-refresh"),
    path(
        "auth/google/",
        Oauth2_views.GoogleCookieLogin.as_view(),
        name="google-cookie-login",
    ),
    path(
        "auth/github/",
        github_auth_views.GitHubCookieLogin.as_view(),
        name="github-login",
    ),
    # ai
    path(
        "api/transcribe-and-reply-2/",
        transcribe_and_reply_2,
        name="transcribe-and-reply_2",
    ),
    # MVP urls for app logics -----------------------------------------------------------
    path("my-profile/", UserProfileDetailUpdateView.as_view(), name="my-profile"),
    path("update-profile/", views.update_profile, name="update-profile"),
    path(
        "friendrequests/",
        FriendRequestListCreateAPIView.as_view(),
        name="friendrequest-list-create",
    ),
    path(
        "friendrequests/<int:pk>/",
        FriendRequestRetrieveUpdateDestroyAPIView.as_view(),
        name="friendrequest-detail",
    ),
    #     ✅ Flow
    # GET /friendrequests/ → List all requests related to current user (incoming + outgoing)
    # POST /friendrequests/ → Send a new request ({"receiver": user_id})
    # PUT /friendrequests/<id>/ → Accept or reject ({"status": "accepted"} or "rejected")
    # DELETE /friendrequests/<id>/ → Cancel or remove request
    path(
        "peer-recommendations/",
        PeerRecommendationAPIView.as_view(),
        name="peer-recommendations",
    ),
    # team lsist apis and other
    path("teams/", TeamListAPIView.as_view(), name="team-list"),
    path(
        "team-join-requests/",
        TeamJoinRequestAPIView.as_view(),
        name="team-join-request",
    ),
    path("team-invitations/", TeamInvitationAPIView.as_view(), name="team-invitation"),
    path(
        "team-invitations/<int:pk>/",
        TeamInvitationUpdateAPIView.as_view(),
        name="team-invitation-update",
    ),
    path("teams/leave/", LeaveTeamAPIView.as_view(), name="leave-team"),
    # create team
    path("teams/create/", TeamCreateAPIView.as_view(), name="team-create"),
    path("teams/<int:pk>/delete/", TeamDeleteAPIView.as_view(), name="team-delete"),
    # Catalog of recommendation at initial profile creation
    path("api/catalog/fields/", FieldListView.as_view(), name="catalog-fields"),
    path(
        "api/catalog/interests/",
        InterestListByFieldView.as_view(),
        name="catalog-interests-by-field",
    ),
    path(
        "api/catalog/skills/",
        SkillListByFieldView.as_view(),
        name="catalog-skills-by-field",
    ),
    # User selection
    path(
        "api/save-skills-interests/",
        SaveSkillsInterestsView.as_view(),
        name="save-skills-interests",
    ),
    path("api/my-selection/", GetMySelectionView.as_view(), name="get-my-selection"),
    # youtube video urls
    path("api/videos/", CourseVideoListCreateView.as_view(), name="video-list-create"),
    path("api/videos/<slug:slug>/", CourseVideoDetailView.as_view(), name="video-detail"),
    path(
        "api/videos/recommended/", RecommendedVideosView.as_view(), name="video-recommended"
    ),
]
