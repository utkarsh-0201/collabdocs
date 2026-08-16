from datetime import date

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related('actor').all().order_by('-created_at')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        """
        Retrieve audit logs with optional filtering by actor and date range.
        
        Supports filtering by:
        - actor_id: Filter logs by the user who performed the action (query param 'actor_id')
        - start_date: Filter logs on or after this date, format YYYY-MM-DD (query param 'start_date')
        - end_date: Filter logs on or before this date, format YYYY-MM-DD (query param 'end_date')
        
        Uses select_related() on actor to avoid N+1 queries.
        Returns logs ordered by creation time in descending order (newest first).
        
        Returns: QuerySet of AuditLog objects with applied filters.
        
        Raises:
            ValueError: If date parameters are in invalid format (caught in list() method).
        """
        queryset = AuditLog.objects.select_related('actor').all()
        actor_id = self.request.query_params.get('actor_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        try:
            if start_date:
                queryset = queryset.filter(created_at__date__gte=date.fromisoformat(start_date))
            if end_date:
                queryset = queryset.filter(created_at__date__lte=date.fromisoformat(end_date))
        except ValueError:
            raise ValueError('Invalid date range provided.')

        if actor_id:
            queryset = queryset.filter(actor_id=actor_id)

        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        List audit logs with pagination and error handling for invalid date filters.
        
        Attempts to retrieve and filter audit logs. If an invalid date is provided,
        catches the ValueError and returns an HTTP 400 error with the error message.
        
        If pagination is configured, returns paginated results; otherwise returns
        all results in a single response.
        
        Returns: Response with audit log list (HTTP 200) or error message (HTTP 400).
        """
        try:
            queryset = self.filter_queryset(self.get_queryset())
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
