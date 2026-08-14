from django.db import transaction
from django.db.models import Count, Max, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from documents.models import Document, DocumentVersion
from documents.serializers import DocumentSerializer, DocumentVersionSerializer, DocumentWriteSerializer
from tags.models import Tag


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related('workspace', 'created_by').prefetch_related('tags', 'versions')
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        """
        Retrieve documents with optimized queries and optional filtering.
        
        Supports filtering by:
        - workspace: Filter by workspace_id (query param 'workspace')
        - status: Filter by document status (query param 'status')
        - tag: Filter by tag name, case-insensitive (query param 'tag')
        - search: Full-text search in title and tag names (query param 'search')
        
        Uses select_related() for workspace and created_by to avoid N+1 queries.
        Uses prefetch_related() for tags and versions for efficient related object loading.
        Uses distinct() to handle multiple joins that could create duplicate results.
        
        Returns: QuerySet of Document objects with applied filters.
        """
        queryset = Document.objects.select_related('workspace', 'created_by').prefetch_related('tags', 'versions')

        workspace_id = self.request.query_params.get('workspace')
        status_filter = self.request.query_params.get('status')
        tag_name = self.request.query_params.get('tag')
        search_text = self.request.query_params.get('search')

        filters = Q()

        if workspace_id:
            filters &= Q(workspace_id=workspace_id)
        if status_filter:
            filters &= Q(status=status_filter)
        if tag_name:
            filters &= Q(tags__name__iexact=tag_name)
        if search_text:
            filters &= Q(title__icontains=search_text) | Q(tags__name__icontains=search_text)

        if filters:
            queryset = queryset.filter(filters)

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        """
        List all documents with applied filters.
        
        Filters the optimized queryset and returns serialized document data.
        
        Returns: Response with list of document objects.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new document with its first version and optional tags in a single transaction.
        
        This operation:
        1. Creates the Document record with title, status, workspace, and creator info.
        2. Creates the first DocumentVersion (version_number=1) with the provided content.
        3. Associates any requested tags (creating them if they don't exist).
        
        All operations are wrapped in transaction.atomic() to ensure consistency: if any
        part fails, the entire document creation is rolled back.
        
        Args:
            request: HTTP request containing document data (workspace, title, status, content, tags).
        
        Returns: Response with the newly created document (HTTP 201).
        """
        serializer = DocumentWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content = serializer.validated_data['content']
        tags_input = serializer.validated_data.get('tags', [])

        with transaction.atomic():
            document = Document.objects.create(
                workspace=serializer.validated_data['workspace'],
                title=serializer.validated_data['title'],
                status=serializer.validated_data['status'],
                created_by=request.user,
            )
            DocumentVersion.objects.create(
                document=document,
                version_number=1,
                content=content,
                created_by=request.user,
            )
            for tag_name in tags_input:
                tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
                document.tags.add(tag)

        response_serializer = DocumentSerializer(document)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Update a document's metadata and optionally create a new version.
        
        When the content is updated:
        1. The Document record is updated with new title, status, and/or workspace.
        2. A new DocumentVersion is created with an incremented version_number.
        3. Previous versions are preserved, allowing full version history tracking.
        
        If content is not provided, only document metadata is updated without creating
        a new version. All operations are wrapped in transaction.atomic() for data consistency.
        
        Args:
            request: HTTP request with partial update data (title, status, workspace, content).
        
        Returns: Response with the updated document.
        """
        instance = self.get_object()
        serializer = DocumentWriteSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        content = serializer.validated_data.get('content')
        new_title = serializer.validated_data.get('title', instance.title)
        new_status = serializer.validated_data.get('status', instance.status)
        new_workspace = serializer.validated_data.get('workspace', instance.workspace)

        with transaction.atomic():
            instance.title = new_title
            instance.status = new_status
            instance.workspace = new_workspace
            instance.save(update_fields=['title', 'status', 'workspace'])

            if content is not None:
                # Determine the next version number by finding the current maximum
                latest_version = DocumentVersion.objects.filter(document=instance).select_for_update().aggregate(
                    max_version=Max('version_number')
                )
                next_version_number = (latest_version['max_version'] or 0) + 1
                DocumentVersion.objects.create(
                    document=instance,
                    version_number=next_version_number,
                    content=content,
                    created_by=request.user,
                )

        response_serializer = DocumentSerializer(instance)
        return Response(response_serializer.data)

    @action(detail=True, methods=['get'], url_path='versions')
    def versions(self, request, *args, **kwargs):
        """
        Retrieve all versions of a document in reverse chronological order.
        
        Returns a list of DocumentVersion objects sorted by version_number in descending
        order, so the most recent version appears first.
        
        Returns: Response with list of document versions.
        """
        document = self.get_object()
        queryset = document.versions.all().order_by('-version_number')
        serializer = DocumentVersionSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='stats')
    def stats(self, request, *args, **kwargs):
        """
        Retrieve statistics about document activity and contributors.
        
        Calculates:
        - version_count: Total number of versions for this document.
        - comment_count: Total number of comments on this document.
        - contributor_count: Number of unique users who have contributed (authored versions or comments).
        
        The contributor_count is computed by merging the sets of version authors and
        comment authors to get a unique user count.
        
        Returns: Response with document statistics.
        """
        document = self.get_object()

        version_count = document.versions.aggregate(count=Count('id', distinct=True))['count'] or 0
        comment_count = document.comments.aggregate(count=Count('id', distinct=True))['count'] or 0

        version_author_ids = set(
            document.versions.exclude(created_by__isnull=True).values_list('created_by_id', flat=True)
        )
        comment_author_ids = set(
            document.comments.exclude(author__isnull=True).values_list('author_id', flat=True)
        )
        contributor_count = len(version_author_ids | comment_author_ids)

        return Response({
            'version_count': version_count,
            'comment_count': comment_count,
            'contributor_count': contributor_count,
        })

    @action(detail=True, methods=['post'], url_path='tags')
    def tags(self, request, *args, **kwargs):
        """
        Add one or more tags to a document.
        
        Accepts a list of tag names and:
        1. Creates any tags that don't already exist (using get_or_create).
        2. Avoids duplicate tag assignments by checking if the tag is already linked.
        3. Bulk-adds all new tags to the document in a single operation.
        
        Validation ensures the request provides a list; individual tag names are trimmed
        and empty names are skipped.
        
        Args:
            request: HTTP request with 'tags' field containing list of tag name strings.
        
        Returns:
            - Response with updated document and tags (HTTP 200) on success.
            - Response with error message (HTTP 400) if tags field is not a list.
        """
        document = self.get_object()
        tag_names = request.data.get('tags', [])
        if not isinstance(tag_names, list):
            return Response({'detail': 'Expected a list of tag names.'}, status=status.HTTP_400_BAD_REQUEST)

        tag_objects = []
        for tag_name in tag_names:
            if not tag_name:
                continue
            tag, _ = Tag.objects.get_or_create(name=str(tag_name).strip())
            if not document.tags.filter(pk=tag.pk).exists():
                tag_objects.append(tag)

        if tag_objects:
            document.tags.add(*tag_objects)

        response_serializer = DocumentSerializer(document)
        return Response(response_serializer.data)
