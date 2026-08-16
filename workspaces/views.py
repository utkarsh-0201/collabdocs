from django.db import IntegrityError, transaction
from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from workspaces.models import Workspace, WorkspaceMember
from workspaces.serializers import (
    WorkspaceMemberCreateSerializer,
    WorkspaceMemberSerializer,
    WorkspaceSerializer,
)


class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = Workspace.objects.select_related('owner').annotate(member_count=Count('members'))
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        """
        Retrieve all workspaces with optimized queries.
        
        Selects owner data in a single query and counts members to avoid N+1 queries.
        Returns: QuerySet of Workspace objects with owner and member_count annotations.
        """
        return Workspace.objects.select_related('owner').annotate(member_count=Count('members'))

    def list(self, request, *args, **kwargs):
        """
        List all workspaces accessible to the authenticated user.
        
        Filters the queryset and returns serialized workspace data with owner and member count.
        Returns: Response with list of workspace objects.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new workspace and automatically add the creator as an admin member.
        
        Uses a transaction.atomic() block to ensure both the workspace and the admin
        membership are created together or not at all, preventing orphaned workspaces.
        
        Args:
            request: HTTP request containing workspace name in the body.
        
        Returns: Response with the newly created workspace (HTTP 201).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            workspace = Workspace.objects.create(
                name=serializer.validated_data['name'],
                owner=request.user,
            )
            WorkspaceMember.objects.create(
                workspace=workspace,
                user=request.user,
                role=WorkspaceMember.Role.ADMIN,
            )

        response_serializer = self.get_serializer(workspace)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='members')
    def members(self, request, *args, **kwargs):
        """
        Retrieve workspace members (GET) or add a new member to the workspace (POST).
        
        GET: Returns a list of all members in the workspace with their roles.
        POST: Adds a new user to the workspace. Only workspace admins can add members.
              Prevents duplicate membership with an IntegrityError handler that returns
              HTTP 409 Conflict if the user is already a member.
        
        Args:
            request: HTTP request (GET or POST) with optional user and role data for POST.
        
        Returns:
            - GET: Response with list of workspace members.
            - POST: Response with the newly added member (HTTP 201) or error (403/409).
        """
        workspace = self.get_object()

        if request.method == 'GET':
            queryset = workspace.members.select_related('user').all()
            serializer = WorkspaceMemberSerializer(queryset, many=True)
            return Response(serializer.data)

        is_admin = WorkspaceMember.objects.filter(
            workspace=workspace,
            user=request.user,
            role=WorkspaceMember.Role.ADMIN,
        ).exists()
        if not is_admin:
            return Response(
                {'detail': 'Only workspace admins can add members.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = WorkspaceMemberCreateSerializer(
            data=request.data,
            context={'request': request, 'workspace': workspace},
        )
        try:
            serializer.is_valid(raise_exception=True)
            member = serializer.save()
        except IntegrityError:
            return Response(
                {'detail': 'User is already a member of this workspace.'},
                status=status.HTTP_409_CONFLICT,
            )

        response_serializer = WorkspaceMemberSerializer(member)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='summary')
    def summary(self, request, *args, **kwargs):
        """
        Retrieve a summary of workspace statistics.
        
        Aggregates document count, total comments, and member count for the workspace.
        Uses distinct=True to avoid double-counting when comments are joined with documents.
        
        Returns: Response with summary statistics (document_count, total_comments, member_count).
        """
        workspace = self.get_object()
        summary = workspace.documents.aggregate(
            document_count=Count('id', distinct=True),
            total_comments=Count('comments', distinct=True),
        )
        summary['member_count'] = workspace.members.count()
        return Response(summary)
