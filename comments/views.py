from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from comments.models import Comment
from comments.serializers import CommentCreateSerializer, CommentSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('author', 'document', 'parent').prefetch_related('replies__author')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        """
        Retrieve comments with optimized queries and optional document filtering.
        
        Uses select_related() for author and document to avoid N+1 queries.
        Uses prefetch_related() for replies and their authors for efficient nested object loading.
        Filters by document_id if the 'document' query parameter is provided.
        
        Returns comments ordered by creation time (oldest first).
        
        Returns: QuerySet of Comment objects with applied filters and optimizations.
        """
        queryset = Comment.objects.select_related('author', 'document', 'parent').prefetch_related('replies__author')
        document_id = self.request.query_params.get('document')
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        return queryset.order_by('created_at')

    def create(self, request, *args, **kwargs):
        """
        Create a new comment on a document.
        
        Validates the comment data and automatically associates the authenticated user
        as the author. The request object is passed in the serializer context to enable
        the author field to be set by the view (not from request body).
        
        Args:
            request: HTTP request containing comment data (document, content, optional parent).
        
        Returns: Response with the newly created comment (HTTP 201).
        """
        serializer = CommentCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(author=request.user)
        response_serializer = CommentSerializer(comment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """
        List comments in a threaded/hierarchical format.
        
        Returns only top-level comments (parent__isnull=True) with all their replies nested
        under a 'replies' key. This transforms the flat comment list into a tree structure
        for better readability in the API response.
        
        Returns: Response with list of comment objects in hierarchical structure.
        """
        queryset = self.filter_queryset(self.get_queryset())
        parents = queryset.filter(parent__isnull=True).prefetch_related('replies__author')
        result = []

        for parent in parents:
            payload = CommentSerializer(parent).data
            payload['replies'] = CommentSerializer(parent.replies.select_related('author').all(), many=True).data
            result.append(payload)

        return Response(result)
