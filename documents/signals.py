from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from audit.models import AuditLog
from documents.models import Document


@receiver(post_save, sender=Document)
def document_audit_log(sender, instance, **kwargs):
    """
    Signal receiver that creates an audit log entry whenever a Document is created or updated.
    
    This handler is triggered by Django's post_save signal after a Document object is saved.
    It automatically logs the action (create or update) with relevant metadata including
    the document's title, workspace, and creator information.
    
    The metadata field stores a JSON object with:
    - model_name: 'Document' (for filtering audit logs by model type)
    - object_id: The UUID of the document
    - title: The document's title
    - workspace_id: The UUID of the workspace containing the document
    
    Uses transaction.atomic() to ensure the audit log is created within the same
    transaction as the document change, maintaining consistency.
    
    Args:
        sender: The Document model class.
        instance: The Document instance that was saved.
        **kwargs: Additional signal arguments (including 'created' flag).
    """
    action = 'created' if instance._state.adding else 'updated'
    with transaction.atomic():
        AuditLog.objects.create(
            actor=instance.created_by,
            action=action,
            target_type='Document',
            target_id=str(instance.pk),
            metadata={
                'model_name': 'Document',
                'object_id': str(instance.pk),
                'title': instance.title,
                'workspace_id': str(instance.workspace_id),
            },
        )
