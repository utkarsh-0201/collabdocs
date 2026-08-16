from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from comments.models import Comment
from documents.models import Document, DocumentVersion
from tags.models import Tag
from workspaces.models import Workspace, WorkspaceMember


class DocumentVersioningAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create(
            first_name='Doc',
            last_name='Owner',
            email='docowner@example.com',
            phone='1111111111',
        )
        self.editor = User.objects.create(
            first_name='Doc',
            last_name='Editor',
            email='doceditor@example.com',
            phone='2222222222',
        )
        self.workspace = Workspace.objects.create(name='Knowledge Base', owner=self.owner)
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.owner,
            role=WorkspaceMember.Role.ADMIN,
        )
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.editor,
            role=WorkspaceMember.Role.EDITOR,
        )
        self.client.force_authenticate(user=self.owner)

    def test_create_document_creates_initial_version_and_returns_nested_version(self):
        payload = {
            'workspace': str(self.workspace.id),
            'title': 'Release Notes',
            'status': Document.Status.DRAFT,
            'content': 'Initial draft text',
        }

        response = self.client.post('/api/documents/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Release Notes')
        self.assertEqual(response.data['latest_version']['version_number'], 1)
        self.assertEqual(response.data['latest_version']['content'], 'Initial draft text')
        self.assertTrue(
            DocumentVersion.objects.filter(
                document_id=response.data['id'],
                version_number=1,
                content='Initial draft text',
            ).exists()
        )

    def test_put_document_creates_new_version_without_overwriting_previous_one(self):
        document = Document.objects.create(
            workspace=self.workspace,
            title='Quarterly Plan',
            status=Document.Status.DRAFT,
            created_by=self.owner,
        )
        DocumentVersion.objects.create(
            document=document,
            version_number=1,
            content='First draft',
            created_by=self.owner,
        )

        response = self.client.put(
            f'/api/documents/{document.id}/',
            {
                'workspace': str(self.workspace.id),
                'title': 'Quarterly Plan',
                'status': Document.Status.PUBLISHED,
                'content': 'Second revision',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['latest_version']['version_number'], 2)
        self.assertEqual(response.data['latest_version']['content'], 'Second revision')
        self.assertEqual(DocumentVersion.objects.filter(document=document).count(), 2)
        self.assertEqual(
            DocumentVersion.objects.get(document=document, version_number=1).content,
            'First draft',
        )

    def test_list_documents_filters_by_workspace_status_tag_and_search(self):
        tag = Tag.objects.create(name='release')
        document = Document.objects.create(
            workspace=self.workspace,
            title='Release Checklist',
            status=Document.Status.DRAFT,
            created_by=self.owner,
        )
        document.tags.add(tag)

        response = self.client.get(
            '/api/documents/?workspace={}&status={}&tag={}&search={}'.format(
                self.workspace.id,
                Document.Status.DRAFT,
                tag.name,
                'checklist',
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Release Checklist')

    def test_get_document_versions_returns_newest_first(self):
        document = Document.objects.create(
            workspace=self.workspace,
            title='Roadmap',
            status=Document.Status.DRAFT,
            created_by=self.owner,
        )
        DocumentVersion.objects.create(
            document=document,
            version_number=1,
            content='v1',
            created_by=self.owner,
        )
        DocumentVersion.objects.create(
            document=document,
            version_number=2,
            content='v2',
            created_by=self.owner,
        )

        response = self.client.get(f'/api/documents/{document.id}/versions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['version_number'], 2)
        self.assertEqual(response.data[1]['version_number'], 1)

    def test_get_document_stats_returns_version_comment_and_contributor_counts(self):
        document = Document.objects.create(
            workspace=self.workspace,
            title='Architecture Notes',
            status=Document.Status.PUBLISHED,
            created_by=self.owner,
        )
        v1 = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            content='version 1',
            created_by=self.owner,
        )
        v2 = DocumentVersion.objects.create(
            document=document,
            version_number=2,
            content='version 2',
            created_by=self.editor,
        )
        Comment.objects.create(document=document, author=self.owner, content='Nice update')
        Comment.objects.create(document=document, author=self.editor, content='Looks good')

        response = self.client.get(f'/api/documents/{document.id}/stats/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version_count'], 2)
        self.assertEqual(response.data['comment_count'], 2)
        self.assertEqual(response.data['contributor_count'], 2)

    def test_post_tags_adds_new_and_existing_tags_without_duplicates(self):
        document = Document.objects.create(
            workspace=self.workspace,
            title='Tagging Demo',
            status=Document.Status.DRAFT,
            created_by=self.owner,
        )
        Tag.objects.create(name='feature')
        document.tags.add(Tag.objects.get(name='feature'))

        response = self.client.post(
            f'/api/documents/{document.id}/tags/',
            {'tags': ['feature', 'release', 'release']},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(document.tags.count(), 2)
        self.assertTrue(document.tags.filter(name='feature').exists())
        self.assertTrue(document.tags.filter(name='release').exists())
