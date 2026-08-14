from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from tags.models import Tag


class TagAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            first_name='Tag',
            last_name='User',
            email='taguser@example.com',
            phone='1111111111',
        )
        self.client.force_authenticate(user=self.user)

    def test_create_tag_creates_new_tag(self):
        response = self.client.post('/api/tags/', {'name': 'urgent'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'urgent')

    def test_create_tag_with_duplicate_name_returns_400(self):
        Tag.objects.create(name='urgent')
        response = self.client.post('/api/tags/', {'name': 'urgent'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', str(response.data).lower())
