import uuid
from django.db import models
from accounts.models import User
from workspaces.models import Workspace


class Document(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_documents',
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'document'


class DocumentVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions',
    )
    content = models.TextField()
    version_number = models.PositiveIntegerField()
    saved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='document_versions',
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document} v{self.version_number}"

    class Meta:
        db_table = 'document_version'