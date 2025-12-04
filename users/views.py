from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import AccessToken

from .serializers import LoginSerializer


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = serializer.validated_data
        identifier = data.get("email") or data.get("username")
        password = data.get("password")

        user = authenticate(request, username=identifier, password=password)
        if not user:
            return Response(
                {"success": False, "message": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = AccessToken.for_user(user)

        user_payload = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "specialty": user.specialty,
        }

        return Response(
            {"success": True, "token": str(token), "user": user_payload},
            status=status.HTTP_200_OK,
        )

