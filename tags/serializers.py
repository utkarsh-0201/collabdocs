from rest_framework import serializers

from tags.models import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

    def validate_name(self, value):
        """
        Validate that the tag name is not empty and is globally unique.
        
        Performs case-insensitive uniqueness check to prevent duplicate tags with
        different cases (e.g., 'Python' and 'python' are treated as the same tag).
        
        Args:
            value: The tag name string to validate.
        
        Returns: The trimmed tag name string.
        
        Raises:
            serializers.ValidationError: If tag name is blank or already exists.
        """
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Tag name cannot be blank.')
        if Tag.objects.filter(name__iexact=cleaned).exists():
            raise serializers.ValidationError('Tag with this name already exists')
        return cleaned
