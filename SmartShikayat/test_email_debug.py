
import os
import django
from django.core.mail import send_mail
from django.conf import settings
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShikayat.settings')
django.setup()

def test_simple_email():
    print(f"Testing basic email connectivity for {settings.EMAIL_HOST_USER}...")
    try:
        send_mail(
            'Debug Test Email',
            'This is a simple test to check if Gmail is blocking us or if credentials are still valid.',
            settings.EMAIL_HOST_USER,
            ['ayushhkadiya@gmail.com'], # Sending to the user who reported the issue
            fail_silently=False,
        )
        print("✅ SUCCESS: Basic email sent successfully.")
    except Exception as e:
        print(f"❌ FAILURE: Could not send email.")
        print(f"Error Details: {e}")

if __name__ == "__main__":
    test_simple_email()
