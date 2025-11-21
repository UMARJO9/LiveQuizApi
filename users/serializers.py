from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
            "specialty",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        required = ["first_name", "last_name", "specialty"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            raise serializers.ValidationError({"detail": f"Отсутствуют обязательные поля: {', '.join(missing)}"})
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password2", None)
        user = User.objects.create_user(password=password, **validated_data)
        return user
