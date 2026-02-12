
import os
import django
import sys

# Setup Django environment
sys.path.append(r'c:\Users\Admin\PycharmProjects\Innovation\SmartShikayat')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShikayat.settings')
django.setup()

from django.contrib.auth import get_user_model
from complaints.models import Complaint

User = get_user_model()

def verify():
    print("Starting verification...")

    # 1. Create a Citizen
    citizen_username = 'citizen_test'
    if not User.objects.filter(username=citizen_username).exists():
        citizen = User.objects.create_user(username=citizen_username, password='password123', role='citizen')
        print(f"Created citizen: {citizen.username}")
    else:
        citizen = User.objects.get(username=citizen_username)
        print(f"Citizen exists: {citizen.username}")

    # 2. Create an Officer
    officer_username = 'officer_water'
    if not User.objects.filter(username=officer_username).exists():
        officer = User.objects.create_user(username=officer_username, password='password123', role='officer', department='water')
        print(f"Created officer: {officer.username} ({officer.department})")
    else:
        officer = User.objects.get(username=officer_username)
        print(f"Officer exists: {officer.username} ({officer.department})")

    # 3. Create a Complaint (Water Issue)
    complaint = Complaint.objects.create(
        user=citizen,
        category='water',
        description='Water leakage on Main St.',
        location='Main St, City Center'
    )
    print(f"Created complaint: {complaint.tracking_id} - Category: {complaint.category}")

    # 4. Verify Auto-Assignment
    if complaint.department == 'water':
        print("[SUCCESS]: Complaint auto-assigned to 'water' department.")
    else:
        print(f"[FAILURE]: Complaint assigned to '{complaint.department}', expected 'water'.")

    # 5. Officer Updates Status
    complaint.status = 'progress'
    complaint.save()
    print(f"Officer updated status to: {complaint.status}")

    # 6. Verify Status
    refreshed_complaint = Complaint.objects.get(id=complaint.id)
    if refreshed_complaint.status == 'progress':
        print("[SUCCESS]: Complaint status updated correctly.")
    else:
        print(f"[FAILURE]: Complaint status is '{refreshed_complaint.status}', expected 'progress'.")

if __name__ == '__main__':
    try:
        verify()
    except Exception as e:
        print(f"[ERROR]: {e}")
