from rest_framework import serializers

from accounts.models import User
from comments.models import Comment


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'email', 'first_name', 'last_name']


class CommentReplySerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    replies = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'document', 'author', 'content', 'parent', 'reply_count', 'replies', 'created_at']
        read_only_fields = ['id', 'document', 'author', 'parent', 'reply_count', 'replies', 'created_at']

    def get_reply_count(self, obj):
        """
        Count the number of direct replies to this comment.
        
        Args:
            obj: The Comment instance.
        
        Returns: Integer count of replies.
        """
        return obj.replies.count()

    def get_replies(self, obj):
        """
        Retrieve and serialize all direct replies to this comment.
        
        Fetches replies using select_related('author') to avoid N+1 queries when
        loading author information for multiple replies.
        
        Args:
            obj: The Comment instance.
        
        Returns: List of serialized reply objects.
        """
        replies = obj.replies.select_related('author').all()
        return CommentReplySerializer(replies, many=True).data


class CommentCreateSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = ['id', 'document', 'content', 'parent', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        """
        Validate comment constraints for threading and document consistency.
        
        Ensures:
        1. If a parent comment is specified, it must belong to the same document.
        2. Nested replies are limited to one level (replies to replies are not allowed).
        
        Args:
            attrs: Dictionary containing validated field data (document, content, parent).
        
        Returns: attrs if all validations pass.
        
        Raises:
            serializers.ValidationError: If parent validation fails.
        """
        document = attrs.get('document')
        parent = attrs.get('parent')

        if parent is not None:
            if parent.document_id != document.id:
                raise serializers.ValidationError({'parent': 'Parent comment must belong to the same document.'})
            if parent.parent_id is not None:
                raise serializers.ValidationError({'parent': 'Nested replies are not allowed beyond one level.'})

        return attrs
