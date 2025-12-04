from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email")
        if not username and not email:
            raise serializers.ValidationError(
                {"detail": "Either 'email' or 'username' is required."}
            )
        if not attrs.get("password"):
            raise serializers.ValidationError({"password": "This field is required."})
        return attrs

