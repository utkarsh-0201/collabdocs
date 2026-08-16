from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from comments.models import Comment
from documents.models import Document
from workspaces.models import Workspace, WorkspaceMember


class CommentAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            first_name='Comment',
            last_name='Author',
            email='commentauthor@example.com',
            phone='1111111111',
        )
        self.other_user = User.objects.create(
            first_name='Other',
            last_name='User',
            email='otheruser@example.com',
            phone='2222222222',
        )
        self.workspace = Workspace.objects.create(name='Comment Workspace', owner=self.user)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role=WorkspaceMember.Role.ADMIN)
        self.document = Document.objects.create(
            workspace=self.workspace,
            title='Comment Document',
            status=Document.Status.DRAFT,
            created_by=self.user,
        )
        self.client.force_authenticate(user=self.user)

    def test_post_comment_creates_top_level_comment_and_reply_count(self):
        response = self.client.post(
            '/api/comments/',
            {'document': str(self.document.id), 'content': 'First comment'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['parent'])
        self.assertEqual(response.data['reply_count'], 0)
        self.assertEqual(Comment.objects.count(), 1)

    def test_post_reply_rejects_parent_from_other_document(self):
        parent = Comment.objects.create(document=self.document, author=self.user, content='Parent')
        other_document = Document.objects.create(
            workspace=self.workspace,
            title='Other Document',
            status=Document.Status.DRAFT,
            created_by=self.user,
        )

        response = self.client.post(
            '/api/comments/',
            {'document': str(other_document.id), 'content': 'Wrong doc reply', 'parent': str(parent.id)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', str(response.data).lower())

    def test_get_comments_lists_threaded_comments_for_document(self):
        parent = Comment.objects.create(document=self.document, author=self.user, content='Top-level comment')
        Comment.objects.create(document=self.document, author=self.other_user, content='Nested reply', parent=parent)

        response = self.client.get(f'/api/comments/?document={self.document.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], 'Top-level comment')
        self.assertEqual(len(response.data[0]['replies']), 1)
        self.assertEqual(response.data[0]['replies'][0]['content'], 'Nested reply')

    def test_get_comments_filters_by_document_and_uses_threading(self):
        other_document = Document.objects.create(
            workspace=self.workspace,
            title='Second Document',
            status=Document.Status.DRAFT,
            created_by=self.user,
        )
        Comment.objects.create(document=self.document, author=self.user, content='First doc comment')
        Comment.objects.create(document=other_document, author=self.user, content='Second doc comment')

        response = self.client.get(f'/api/comments/?document={self.document.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], 'First doc comment')
