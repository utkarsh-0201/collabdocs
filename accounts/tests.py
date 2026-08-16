from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User


class UserAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            first_name='Jane',
            last_name='Doe',
            email='jane@example.com',
            phone='1234567890',
        )

    def test_create_user_returns_201_and_payload(self):
        payload = {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john@example.com',
            'phone': '9876543210',
        }

        response = self.client.post('/users/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], payload['email'])
        self.assertEqual(response.data['first_name'], payload['first_name'])

    def test_get_user_by_id_returns_200(self):
        response = self.client.get(f'/users/{self.user.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.user.id))
        self.assertEqual(response.data['email'], self.user.email)

    def test_get_missing_user_returns_404_message(self):
        missing_id = '00000000-0000-0000-0000-000000000999'

        response = self.client.get(f'/users/{missing_id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('User', str(response.data))
