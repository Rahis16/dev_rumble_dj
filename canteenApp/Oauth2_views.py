# views.py
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from datetime import datetime
import json
import base64

User = get_user_model()


class GoogleCookieLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

    def get_response(self):
        response = super().get_response()
        
        print("google login view hit!")

        user = self.user
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Public info
        public_data = {
            "is_authenticated": True,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "username": user.username,
        }

        max_age = int(access["exp"] - datetime.utcnow().timestamp())
        public_data_json = json.dumps(public_data, separators=(',', ':'))
        public_data_base64 = base64.b64encode(public_data_json.encode()).decode()

        # ✅ Set Cookies like your normal login
        response.set_cookie(
            key='access_token',
            value=str(access),
            httponly=True,
            secure=True,  # use True in prod
            samesite='None',
            path='/',
            max_age=max_age
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite='None',
            path='/',
            max_age=86400
        )
        response.set_cookie(
            key='user_status',
            value=public_data_base64,
            httponly=False,
            secure=True,
            samesite='None',
            path='/',
            max_age=max_age
        )

        return response
