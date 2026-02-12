
import os
import django
import sys
# Make sure we can find the project root
sys.path.append(os.getcwd())
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShikayat.settings')
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from accounts.models import User

# List of dummy users to create
# Format: Vehicle Number, Username/Name, Email, Phone
DUMMY_DATA = [
    ("KA53P3307", "Kadiya Ayush H", "ayushhkadiya@gmail.com", "9876543210"),
    ("GJ01AB1234", "Rajesh Kumar", "rajesh@example.com", "9876543211"),
    ("MH12CD5678", "Priya Sharma", "priya@example.com", "9876543212"),
    ("DL3CDE9012", "Amit Patel", "amit@example.com", "9876543213"),
    ("GJ05XY9876", "Sneha Gupta", "sneha@example.com", "9876543214"),
]

print("Starting to seed dummy vehicle owners...")

for plate, name, email, phone in DUMMY_DATA:
    # Username needs to be unique and alphanumeric-ish usually
    username = name.replace(" ", "_").lower()
    
    # Try to get or create
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'role': 'citizen',
            'phone': phone,
            'vehicle_number': plate
        }
    )
    
    if created:
        user.set_password("password123")
        user.save()
        print(f"[CREATED] User: {name} ({username}) | Plate: {plate} | Email: {email}")
    else:
        # Check vehicle number mismatch logic if necessary, or update
        if user.vehicle_number != plate:
            print(f"[EXISTS] User {username} exists. Updating plate from {user.vehicle_number} to {plate}.")
            user.vehicle_number = plate
            user.save()
        else:
            print(f"[EXISTS] User: {name} | Plate: {plate} matches.")

print("Seeding complete.")

from accounts.models import User

# List of dummy users to create
# Format: Vehicle Number, Username/Name, Email, Phone
DUMMY_DATA = [
    ("KA53P3307", "Kadiya Ayush H", "ayushhkadiya@gmail.com", "9876543210"),
    ("GJ01AB1234", "Rajesh Kumar", "rajesh@example.com", "9876543211"),
    ("MH12CD5678", "Priya Sharma", "priya@example.com", "9876543212"),
    ("DL3CDE9012", "Amit Patel", "amit@example.com", "9876543213"),
    ("GJ05XY9876", "Sneha Gupta", "sneha@example.com", "9876543214"),
]

print("Starting to seed dummy vehicle owners...")

for plate, name, email, phone in DUMMY_DATA:
    # Username needs to be unique and alphanumeric-ish usually, let's derive from name
    username = name.replace(" ", "_").lower()
    
    # Check if user exists by vehicle number or username
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'role': 'citizen',
            'vehicle_number': plate,
            'phone': phone
        }
    )
    
    if created:
        user.set_password("password123") # Default password
        user.save()
        print(f"[CREATED] User: {name} | Plate: {plate} | Email: {email}")
    else:
        # Update existing user if needed (e.g. to matching plate/email)
        if user.vehicle_number != plate:
            print(f"[Exists] User {username} exists but plate mismatch. Skipping update to avoid conflicts.")
        else:
            print(f"[EXISTS] User: {name} | Plate: {plate} matches.")

print("Seeding complete.")
