from django.db import IntegrityError
from rest_framework import serializers

from accounts.models import User
from workspaces.models import Workspace, WorkspaceMember


class UserMiniSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id', 'username', 'email']

    def get_username(self, obj):
        """
        Generate a display username for the user object.
        
        Returns the user's username field if available, otherwise extracts the email
        prefix, or falls back to the user's ID string. This ensures a display name
        is always available even if some fields are missing.
        
        Args:
            obj: User instance.
        
        Returns: String representing the user's username or email prefix.
        """
        """
        Generate a display username for the user object.
        
        Returns the user's username field if available, otherwise extracts the email
        prefix, or falls back to the user's ID string. This ensures a display name
        is always available even if some fields are missing.
        
        Args:
            obj: User instance.
        
        Returns: String representing the user's username or email prefix.
        """
        if getattr(obj, 'username', None):
            return obj.username
        if obj.email:
            return obj.email.split('@')[0]
        return str(obj.id)


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = UserMiniSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Workspace
        fields = ['id', 'name', 'owner', 'created_at', 'member_count']
        read_only_fields = ['id', 'created_at', 'owner', 'member_count']


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ['id', 'workspace', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'workspace', 'user', 'joined_at']


class WorkspaceMemberCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = WorkspaceMember
        fields = ['user', 'role']

    def validate(self, attrs):
        """
        Validate that the actor adding a member is an admin and the user is not already a member.
        
        Ensures:
        1. The requesting user (actor) is an admin of the workspace.
        2. The target user is not already a member (prevents duplicate membership).
        
        Args:
            attrs: Dictionary containing validated field data (user, role).
        
        Returns: attrs if all validations pass.
        
        Raises:
            serializers.ValidationError: If actor is not an admin or user is already a member.
        """
        workspace = self.context['workspace']
        actor = self.context['request'].user

        is_admin = WorkspaceMember.objects.filter(
            workspace=workspace,
            user=actor,
            role=WorkspaceMember.Role.ADMIN,
        ).exists()
        if not is_admin:
            raise serializers.ValidationError({'detail': 'Only workspace admins can add members.'})

        user = attrs['user']
        if WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise serializers.ValidationError({'user': 'User is already a member of this workspace.'})

        return attrs

    def create(self, validated_data):
        """
        Create a new WorkspaceMember, handling potential IntegrityError from race conditions.
        
        Although the validate() method checks for existing members, a race condition between
        validation and creation can still occur. This method catches IntegrityError and
        converts it to a ValidationError for consistent error reporting.
        
        Args:
            validated_data: Dictionary with 'user' and 'role' keys.
        
        Returns: The newly created WorkspaceMember instance.
        
        Raises:
            serializers.ValidationError: If an IntegrityError occurs (user already a member).
        """
        workspace = self.context['workspace']
        try:
            return WorkspaceMember.objects.create(
                workspace=workspace,
                **validated_data,
            )
        except IntegrityError:
            raise serializers.ValidationError({'user': 'User is already a member of this workspace.'})
