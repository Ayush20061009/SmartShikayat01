
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShikayat.settings')
django.setup()

from accounts.models import User
from complaints.models import Complaint

print("-" * 50)
print("USERS (id, username, role, area, vehicle_number, wallet)")
print("-" * 50)
users = User.objects.all()
for u in users:
    print(f"{u.id} | {u.username} | {u.role} | {u.area} | {u.vehicle_number} | {u.wallet_balance}")

print("\n" + "-" * 80)
print("COMPLAINTS (id, category, location, vehicle, fine_amt, paid?, reporter_earning)")
print("-" * 80)
complaints = Complaint.objects.all()
for c in complaints:
    print(f"{c.id} | {c.category} | {c.location} | {c.vehicle_number} | {c.fine_amount} | {c.fine_paid} | {c.reporter_earning}")

print("\n" + "-" * 50)
print("NOTIFICATIONS (id, user, message, is_read)")
print("-" * 50)
from notifications.models import Notification
notifications = Notification.objects.all()
for n in notifications:
    print(f"{n.id} | {n.user.username} | {n.message} | {n.is_read}")
