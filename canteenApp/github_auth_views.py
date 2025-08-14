# views.py
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from datetime import datetime

User = get_user_model()

class GitHubCookieLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    
    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        if not code:
            return Response({"error": "Missing code"}, status=400)

        # Exchange code for access token
        client_id = 'Ov23li2EaARy6c1mz8NK'
        client_secret = '6fce52903bb75ac5adaaf9de939353abc81cce70'
        token_url = "https://github.com/login/oauth/access_token"

        token_res = requests.post(token_url, data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
        }, headers={'Accept': 'application/json'})

        token_data = token_res.json()
        access_token = token_data.get('access_token')

        if not access_token:
            return Response({"error": "Failed to get access token"}, status=400)

        # Replace 'access_token' in request.data to pass to adapter
        request.data['access_token'] = access_token

        # Call the usual SocialLoginView.post() with the updated data
        return super().post(request, *args, **kwargs)

    def get_response(self):
        response = super().get_response()
        
        print("✅ GitHub login view hit!")

        user = self.user
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        max_age = int(access["exp"] - datetime.utcnow().timestamp())

        # ✅ Set cookies (same as Google flow)
        response.set_cookie(
            key='access_token',
            value=str(access),
            httponly=True,
            secure=True,  # 🔒 Set to True in production
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
            max_age=86400  # 1 day
        )
        
        return response
