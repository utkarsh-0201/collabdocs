from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('created_at')
    serializer_class = UserSerializer
    lookup_field = 'id'

    def list(self, request, *args, **kwargs):
        uid = request.query_params.get('uid')
        if uid:
            user = get_object_or_404(User, id=uid)
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'detail': 'Invalid user data.',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        response_serializer = self.get_serializer(user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception:
            return Response(
                {'detail': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='by-email')
    def by_email(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response(
                {'detail': 'Email query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(User, email__iexact=email)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='by-uid')
    def by_uid(self, request):
        uid = request.query_params.get('uid')
        if not uid:
            return Response(
                {'detail': 'UID query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(User, id=uid)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


