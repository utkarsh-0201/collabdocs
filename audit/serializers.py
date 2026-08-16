from rest_framework import serializers

from accounts.models import User
from audit.models import AuditLog


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'email', 'first_name', 'last_name']


class AuditLogSerializer(serializers.ModelSerializer):
    actor = UserMiniSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'actor', 'action', 'target_type', 'target_id', 'metadata', 'created_at']
        read_only_fields = ['id', 'actor', 'created_at']
