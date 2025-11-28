from django.shortcuts import render

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from backend.responses import StandardResponseMixin

from .serializers import RegisterSerializer


class RegisterView(StandardResponseMixin, generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        data = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "specialty": user.specialty,
            },
        }
        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            "user": {
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "specialty": self.user.specialty,
            }
        })
        return data


class CustomTokenObtainPairView(StandardResponseMixin, TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(StandardResponseMixin, TokenRefreshView):
    pass

