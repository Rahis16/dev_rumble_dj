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
            secure=True,      # False only for local dev with http
            samesite='Lax',
            max_age=300       # 5 minutes
        )

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=True,
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
    permission_classes = []  # We'll handle auth manually

    def get(self, request):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')

        try:
            # Try validating access token
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
            })

        except Exception:
            # Access token is expired or invalid
            if not refresh_token:
                return Response({'authenticated': False}, status=401)

            try:
                refresh = RefreshToken(refresh_token)
                user_id = refresh['user_id']
                user = User.objects.get(id=user_id)

                # Generate new access token
                new_access_token = str(refresh.access_token)

                response = Response({
                    "authenticated": True,
                    "username": user.username,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                    "email": user.email,
                    "wallet_balance": str(user.wallet.balance) if hasattr(user, 'wallet') else "0",
                    "photo": user.profile.profile_pic.url if user.profile.profile_pic else None,
                })

                # Set new access token cookie
                response.set_cookie(
                    key='access_token',
                    value=new_access_token,
                    httponly=True,
                    secure=True,
                    samesite='None',
                    max_age=60 * 15  # 15 minutes
                )
                return response

            except TokenError:
                return Response({'authenticated': False}, status=401)
