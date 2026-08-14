from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_first_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('First name is required.')
        return value.strip()

    def validate_last_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('Last name is required.')
        return value.strip()

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        existing_user = User.objects.filter(email__iexact=normalized_email)
        if self.instance:
            existing_user = existing_user.exclude(pk=self.instance.pk)
        if existing_user.exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return normalized_email

    def validate_phone(self, value):
        normalized_phone = value.strip()
        existing_user = User.objects.filter(phone=normalized_phone)
        if self.instance:
            existing_user = existing_user.exclude(pk=self.instance.pk)
        if existing_user.exists():
            raise serializers.ValidationError('A user with this phone number already exists.')
        return normalized_phone
