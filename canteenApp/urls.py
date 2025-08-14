from django.urls import path, include
from . import views
from .import auth_views
from .auth_views import CookieLoginView, CookieLogoutView
from . import Oauth2_views
from . import github_auth_views

urlpatterns = [
    # path('', views.home, name="home"),
    
    # drf jwt auth urls
    path('auth/login/', CookieLoginView.as_view(), name='rest_login'),
    path('auth/logout/', CookieLogoutView.as_view(), name='rest_logout'),
    path('auth/', include('dj_rest_auth.registration.urls')),  # Signup
    path('auth/status/', auth_views.AuthStatusView.as_view(), name='auth-status'),
    path('token/refresh/', auth_views.RefreshTokenView.as_view(), name='token-refresh'),
    path("auth/google/", Oauth2_views.GoogleCookieLogin.as_view(), name="google-cookie-login"),
    path("auth/github/", github_auth_views.GitHubCookieLogin.as_view(), name="github-login"),
]
     