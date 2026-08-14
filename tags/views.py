from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tags.models import Tag
from tags.serializers import TagSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def create(self, request, *args, **kwargs):
        """
        Create a new tag.
        
        Validates tag data (ensuring name is unique and not blank) before creation.
        Returns the created tag with its serialized data.
        
        Args:
            request: HTTP request containing tag data (name).
        
        Returns: Response with the newly created tag (HTTP 201).
        
        Note: Tag name validation (uniqueness, blank check) is performed in the serializer.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tag = serializer.save()
        return Response(self.get_serializer(tag).data, status=status.HTTP_201_CREATED)
