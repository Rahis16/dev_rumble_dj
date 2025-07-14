from rest_framework.response import Response
from rest_framework.views import APIView
from dj_rest_auth.views import LoginView
from rest_framework_simplejwt.tokens import RefreshToken
from dj_rest_auth.views import LogoutView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

User = get_user_model()


class CookieLoginView(LoginView):
    def get_response(self):
        response = super().get_response()

        # ✅ Create refresh + access tokens
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token

        # ✅ Set HttpOnly cookies
        response.set_cookie(
            key='access_token',
            value=str(access),
            httponly=True,
            secure=False,      # False only for local dev with http
            samesite='Lax',
            max_age=300       # 5 minutes
        )

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=86400     # 1 day
        )

        return response

    
    

class CookieLogoutView(LogoutView):
    def logout(self, request):
        response = super().logout(request)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response    



class AuthStatusView(APIView):
    permission_classes = []

    def get(self, request):
        access_token = request.COOKIES.get('access_token')

        try:
            token = AccessToken(access_token)
            user_id = token['user_id']
            user = User.objects.get(id=user_id)

            return Response({
                "authenticated": True,
                "username": user.username,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "email": user.email,
                "wallet_balance": str(user.wallet.balance) if hasattr(user, 'wallet') else "0",
                "photo": user.profile.profile_pic.url if user.profile.profile_pic else None,
                "exp": token["exp"],  # send token expiry to frontend
            })

        except Exception:
            return Response({'authenticated': False}, status=401)



class RefreshTokenView(APIView):
    permission_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'Refresh token missing'}, status=401)

        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh['user_id']
            user = User.objects.get(id=user_id)
            access_token = str(refresh.access_token)

            response = Response({'message': 'Token refreshed'})
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=60 * 15
            )
            return response

        except TokenError:
            return Response({'detail': 'Invalid refresh token'}, status=401)
