from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from audit.models import AuditLog


class AuditLogAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.actor = User.objects.create(
            first_name='Actor',
            last_name='User',
            email='actor@example.com',
            phone='1111111111',
        )
        self.other_actor = User.objects.create(
            first_name='Other',
            last_name='User',
            email='otheractor@example.com',
            phone='2222222222',
        )
        self.client.force_authenticate(user=self.actor)

    def test_get_audit_logs_lists_recent_entries(self):
        AuditLog.objects.create(actor=self.actor, action='created_document', target_type='Document', target_id=1)
        AuditLog.objects.create(actor=self.other_actor, action='added_member', target_type='Workspace', target_id=2)

        response = self.client.get('/api/audit-logs/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 2)

    def test_get_audit_logs_filters_by_actor_id_and_date_range(self):
        log = AuditLog.objects.create(actor=self.actor, action='updated_document', target_type='Document', target_id=9)
        response = self.client.get(
            f'/api/audit-logs/?actor_id={self.actor.id}&start_date={log.created_at.date()}&end_date={log.created_at.date()}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['action'], 'updated_document')

    def test_get_audit_logs_rejects_invalid_date_range(self):
        response = self.client.get('/api/audit-logs/?start_date=2026-02-30&end_date=2026-03-01')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
