import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShikayat.settings')
django.setup()

from accounts.models import User

output = []
output.append("=" * 80)
output.append("USER EMAILS IN DATABASE")
output.append("=" * 80)
output.append("")

users = User.objects.all()

if not users:
    output.append("No users found in database.")
else:
    output.append(f"Total Users: {users.count()}")
    output.append("")
    
    for i, user in enumerate(users, 1):
        output.append(f"{i}. {user.username}")
        output.append(f"   Email: {user.email}")
        output.append(f"   Role: {user.role}")
        output.append(f"   Vehicle: {user.vehicle_number or 'N/A'}")
        output.append(f"   Phone: {user.phone or 'N/A'}")
        output.append("")

output.append("=" * 80)

# Print to console
for line in output:
    print(line)

# Save to file
with open('user_emails.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("\nData saved to user_emails.txt")
