from rest_framework.test import APITestCase
from django.urls import reverse
from .models import Hospital, User

class HospitalRegistrationTests(APITestCase):
    def test_hospital_registration(self):
        url = reverse('hospital-register')
        data = {
            'name': 'Test Hospital',
            'registration_number': 'TEST123',
            'address': '123 Test Street',
            'primary_phone': '08011111111',
            'secondary_phone': '08022222222',
            'emergency_phone': '08033333333',
            'email': 'hospital@test.com',
            'total_beds': 100,
            'admin_email': 'admin@test.com',
            'admin_password': 'TestPass123!',
            'admin_phone': '08044444444',
            'admin_first_name': 'Test',
            'admin_last_name': 'Admin'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Hospital.objects.count(), 1)
        self.assertEqual(User.objects.filter(user_type='HOSPITAL_ADMIN').count(), 1)