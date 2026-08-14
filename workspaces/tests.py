from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from comments.models import Comment
from documents.models import Document
from workspaces.models import Workspace, WorkspaceMember


class WorkspaceAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create(
            first_name='Alice',
            last_name='Admin',
            email='alice@example.com',
            phone='1111111111',
        )
        self.editor = User.objects.create(
            first_name='Bob',
            last_name='Editor',
            email='bob@example.com',
            phone='2222222222',
        )
        self.viewer = User.objects.create(
            first_name='Cara',
            last_name='Viewer',
            email='cara@example.com',
            phone='3333333333',
        )
        self.workspace = Workspace.objects.create(name='Product Docs', owner=self.owner)
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.owner,
            role=WorkspaceMember.Role.ADMIN,
        )
        self.client.force_authenticate(user=self.owner)

    def test_create_workspace_creates_owner_member_and_returns_owner_details(self):
        payload = {'name': 'Launch Plan'}

        response = self.client.post('/api/workspaces/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Launch Plan')
        self.assertEqual(response.data['owner']['email'], self.owner.email)
        self.assertTrue(
            WorkspaceMember.objects.filter(
                workspace_id=response.data['id'],
                user=self.owner,
                role=WorkspaceMember.Role.ADMIN,
            ).exists()
        )

    def test_get_workspace_detail_includes_member_count(self):
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.editor,
            role=WorkspaceMember.Role.EDITOR,
        )

        response = self.client.get(f'/api/workspaces/{self.workspace.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['member_count'], 2)

    def test_add_member_as_admin_creates_member_record(self):
        payload = {
            'user': str(self.editor.id),
            'role': WorkspaceMember.Role.EDITOR,
        }

        response = self.client.post(
            f'/api/workspaces/{self.workspace.id}/members/',
            payload,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], WorkspaceMember.Role.EDITOR)
        self.assertEqual(response.data['user']['email'], self.editor.email)

    def test_add_member_duplicate_returns_400(self):
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.editor,
            role=WorkspaceMember.Role.VIEWER,
        )
        payload = {
            'user': str(self.editor.id),
            'role': WorkspaceMember.Role.ADMIN,
        }

        response = self.client.post(
            f'/api/workspaces/{self.workspace.id}/members/',
            payload,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already a member', str(response.data).lower())

    def test_missing_workspace_returns_404_when_adding_member(self):
        missing_id = '00000000-0000-0000-0000-000000000999'

        response = self.client.post(
            f'/api/workspaces/{missing_id}/members/',
            {'user': str(self.editor.id), 'role': WorkspaceMember.Role.VIEWER},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_admin_cannot_add_member(self):
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.editor,
            role=WorkspaceMember.Role.EDITOR,
        )
        self.client.force_authenticate(user=self.editor)
        payload = {
            'user': str(self.viewer.id),
            'role': WorkspaceMember.Role.VIEWER,
        }

        response = self.client.post(
            f'/api/workspaces/{self.workspace.id}/members/',
            payload,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('admin', str(response.data).lower())

    def test_list_members_returns_nested_user_and_role(self):
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.editor,
            role=WorkspaceMember.Role.EDITOR,
        )

        response = self.client.get(f'/api/workspaces/{self.workspace.id}/members/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['user']['email'] == self.owner.email for item in response.data))
        self.assertTrue(any(item['role'] == WorkspaceMember.Role.EDITOR for item in response.data))

    def test_workspace_summary_returns_document_and_comment_counts(self):
        doc_one = Document.objects.create(
            title='Alpha',
            content='First doc',
            workspace=self.workspace,
            created_by=self.owner,
            status=Document.Status.DRAFT,
        )
        doc_two = Document.objects.create(
            title='Beta',
            content='Second doc',
            workspace=self.workspace,
            created_by=self.editor,
            status=Document.Status.DRAFT,
        )
        Comment.objects.create(document=doc_one, author=self.owner, content='Nice')
        Comment.objects.create(document=doc_two, author=self.editor, content='Looks great')
        Comment.objects.create(document=doc_one, author=self.editor, content='Second comment')

        response = self.client.get(f'/api/workspaces/{self.workspace.id}/summary/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['document_count'], 2)
        self.assertEqual(response.data['member_count'], 1)
        self.assertEqual(response.data['total_comments'], 3)
