
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.core import mail
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Complaint
from .forms import ComplaintForm

User = get_user_model()

class IllegalParkingEmailTests(TestCase):
    
    def setUp(self):
        # 1. Create Users
        # Officer
        self.officer = User.objects.create_user(username='Officer', email='officer@test.com', password='password', role='officer', department='traffic')
        # Reporter
        self.reporter = User.objects.create_user(username='Reporter', email='reporter@test.com', password='password')
        # Vehicle Owner (The one getting fined)
        self.vehicle_number = "MH03BW1690"
        self.owner = User.objects.create_user(username='AK', email='ayushhkadiya@gmail.com', password='password', vehicle_number=self.vehicle_number)
        
        # 2. Setup Client
        self.client = Client()
        
        # 3. Create dummy image correctly
        from io import BytesIO
        self.test_image = BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0aIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
        self.test_image.name = 'illegal_parking.png'

    @patch('complaints.views.check_image_ai')
    @patch('complaints.views.check_illegal_parking_ai')
    @patch('complaints.views.extract_license_plate')
    def test_case_1_happy_path_ai_detects_owner_emails_sent(self, mock_extract, mock_check_illegal, mock_check_ai):
        """
        Scenario: AI detects illegal parking + extracts correct plate -> Owner receives email.
        """
        # Login
        self.client.login(username='Reporter', password='password')
        
        # Use simple returns to simulate view logic
        # Mocking check_image_ai to return (False, "Real photo") -> Not fake/AI generated
        mock_check_ai.return_value = (False, "Real Image")
        # Mocking check_illegal_parking_ai -> (True, "Blocking road")
        mock_check_illegal.return_value = (True, "Blocking road")
        # Mocking extract_license_plate -> "MH03BW1690"
        mock_extract.return_value = self.vehicle_number
        
        # Submit
        response = self.client.post(reverse('complaint_create'), {
            'category': 'parking',
            'description': 'Illegal parking test',
            'location': 'Downtown',
            'image': self.test_image
        }, follow=True)
        
        # Check Response for redirect or success
        self.assertRedirects(response, reverse('complaint_list'))
        
        # Check Email Sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.vehicle_number, mail.outbox[0].subject)
        self.assertIn("ayushhkadiya@gmail.com", mail.outbox[0].to)
        print("Test Case 1 Passed: Complaint created, Owner emailed successfully.")

    @patch('complaints.views.check_image_ai')
    @patch('complaints.views.check_illegal_parking_ai')
    @patch('complaints.views.extract_license_plate')
    def test_case_2_manual_override_ai_fails(self, mock_extract, mock_check_illegal, mock_check_ai):
        """
        Scenario: AI fails to read plate (None), User enters manually -> Owner receives email.
        """
        self.client.login(username='Reporter', password='password')
        
        mock_check_ai.return_value = (False, "Real Image")
        mock_check_illegal.return_value = (True, "Yes Illegal")
        # AI Fails
        mock_extract.return_value = None 
        
        response = self.client.post(reverse('complaint_create'), {
            'category': 'parking',
            'description': 'Manual override test',
            'location': 'Market',
            'image': self.test_image,
            'manual_vehicle_number': self.vehicle_number # User enters manually
        }, follow=True)
        
        self.assertRedirects(response, reverse('complaint_list'))
        
        # Check if email sent (Should use manual number)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.vehicle_number, mail.outbox[0].subject)
        print("Test Case 2 Passed: AI Failed, Manual Entry Sent Email.")

    @patch('complaints.views.check_image_ai')
    @patch('complaints.views.check_illegal_parking_ai')
    @patch('complaints.views.extract_license_plate')
    def test_case_3_owner_not_found(self, mock_extract, mock_check_illegal, mock_check_ai):
        """
        Scenario: Plate detected "MH99ZZ0000" (No owner) -> Should show error on form.
        """
        self.client.login(username='Reporter', password='password')
        
        mock_check_ai.return_value = (False, "Real Image")
        mock_check_illegal.return_value = (True, "Yes Illegal")
        mock_extract.return_value = "MH99ZZ0000" # Unknown vehicle
        
        response = self.client.post(reverse('complaint_create'), {
            'category': 'parking',
            'description': 'Unknown vehicle test',
            'location': 'Suburbs',
            'image': self.test_image
        })
        
        # Should stay on page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not found")
        self.assertContains(response, "MH99ZZ0000")
        # No email sent
        self.assertEqual(len(mail.outbox), 0)
        print("Test Case 3 Passed: Unknown Vehicle blocked correctly.")

    @patch('complaints.views.check_image_ai')
    @patch('complaints.views.check_illegal_parking_ai')
    @patch('complaints.views.extract_license_plate')
    def test_case_4_ai_mismatch_strict(self, mock_extract, mock_check_illegal, mock_check_ai):
        """
        Scenario: AI reads 'MH01AB1111', User enters 'MH03BW1690' -> Should flag mismatch error.
        """
        self.client.login(username='Reporter', password='password')
        
        mock_check_ai.return_value = (False, "Real Image")
        mock_check_illegal.return_value = (True, "Yes Illegal")
        mock_extract.return_value = "MH01AB1111" # AI sees this
        
        response = self.client.post(reverse('complaint_create'), {
            'category': 'parking',
            'description': 'Mismatch test',
            'location': 'City',
            'image': self.test_image,
            'manual_vehicle_number': self.vehicle_number # User tries to input differnt
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mismatch")
        self.assertEqual(len(mail.outbox), 0)
        print("Test Case 4 Passed: AI vs Manual Mismatch detected.")

    @patch('complaints.views.send_fine_email')
    @patch('complaints.views.check_image_ai')
    @patch('complaints.views.check_illegal_parking_ai')
    @patch('complaints.views.extract_license_plate')
    def test_case_5_resend_email_officer(self, mock_extract, mock_check_illegal, mock_check_ai, mock_send_email):
        """
        Scenario: Officer clicks 'Resend Email' -> Sends email manually.
        """
        # Create complaint first (without email logic for setup speed)
        dept = 'traffic'
        complaint = Complaint.objects.create(
            user=self.reporter, 
            category='parking', 
            description='Resend test', 
            location='Main St', 
            status='pending',
            department=dept,
            vehicle_number=self.vehicle_number,
            fine_amount=100.00
        )
        
        # Setup mock for send_fine_email to return Success
        mock_send_email.return_value = (True, "Email sent successfully")

        # Login as Officer
        self.client.login(username='Officer', password='password')
        
        response = self.client.get(reverse('resend_fine_email', kwargs={'tracking_id': complaint.tracking_id}), follow=True)
        
        self.assertRedirects(response, reverse('officer_dashboard'))
        # Messages check if possible, or verify mock called
        mock_send_email.assert_called_once()
        print("Test Case 5 Passed: Officer Resend Email triggered.")

