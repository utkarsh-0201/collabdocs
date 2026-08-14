from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from audit.models import AuditLog
from workspaces.models import WorkspaceMember


@receiver(post_save, sender=WorkspaceMember)
def workspacemember_audit_log(sender, instance, **kwargs):
    """
    Signal receiver that creates an audit log entry whenever a WorkspaceMember is added.
    
    This handler is triggered by Django's post_save signal after a WorkspaceMember object
    is created. It automatically logs the membership addition with metadata including
    the workspace ID, user ID, and the role assigned (e.g., 'admin', 'member').
    
    The metadata field stores a JSON object with:
    - workspace_id: The UUID of the workspace
    - user_id: The UUID of the user being added
    - role: The role assigned to the member ('admin' or 'member')
    
    Uses transaction.atomic() to ensure the audit log is created within the same
    transaction as the membership change, maintaining consistency.
    
    Args:
        sender: The WorkspaceMember model class.
        instance: The WorkspaceMember instance that was saved (the new member).
        **kwargs: Additional signal arguments (including 'created' flag).
    """
    with transaction.atomic():
        AuditLog.objects.create(
            actor=instance.user,
            action='added_member',
            target_type='Workspace',
            target_id=str(instance.workspace_id),
            metadata={
                'workspace_id': str(instance.workspace_id),
                'user_id': str(instance.user_id),
                'role': instance.role,
            },
        )
