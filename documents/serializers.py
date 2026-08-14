from rest_framework import serializers

from accounts.models import User
from documents.models import Document, DocumentVersion
from tags.models import Tag


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'email', 'first_name', 'last_name']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class DocumentVersionSerializer(serializers.ModelSerializer):
    created_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = DocumentVersion
        fields = ['id', 'document', 'version_number', 'content', 'created_by', 'created_at']
        read_only_fields = ['id', 'document', 'created_by', 'created_at']


class DocumentWriteSerializer(serializers.ModelSerializer):
    content = serializers.CharField(required=True, write_only=True)
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Document
        fields = ['id', 'workspace', 'title', 'status', 'created_by', 'content', 'tags']
        read_only_fields = ['id', 'created_by']

    def validate_title(self, value):
        """
        Validate that the document title is not empty or whitespace-only.
        
        Strips leading and trailing whitespace from the title.
        
        Args:
            value: The title string to validate.
        
        Returns: The stripped title string.
        
        Raises:
            serializers.ValidationError: If title is empty or contains only whitespace.
        """
        if not value.strip():
            raise serializers.ValidationError('Document title is required.')
        return value.strip()


class DocumentSerializer(serializers.ModelSerializer):
    workspace = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = UserMiniSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    latest_version = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'workspace', 'title', 'status', 'created_by', 'created_at', 'updated_at', 'tags', 'latest_version']
        read_only_fields = ['id', 'workspace', 'created_by', 'created_at', 'updated_at', 'tags', 'latest_version']

    def get_latest_version(self, obj):
        """
        Retrieve the most recent version of the document.
        
        Queries for the DocumentVersion with the highest version_number and returns
        it in serialized form. Returns None if the document has no versions.
        
        Args:
            obj: The Document instance.
        
        Returns: Serialized DocumentVersion data or None if no versions exist.
        """
        latest = obj.versions.order_by('-version_number').first()
        if latest is None:
            return None
        return DocumentVersionSerializer(latest).data
