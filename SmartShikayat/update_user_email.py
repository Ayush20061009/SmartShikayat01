import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShikayat.settings')
django.setup()

from accounts.models import User

username = "Tirth_Pagi"
new_email = "ayushhkadiya@gmail.com" # Using your preferred testing email

try:
    user = User.objects.get(username=username)
    print(f"Current email for {user.username}: '{user.email}'")
    
    user.email = new_email
    user.save()
    
    print(f"✅ Updated email for {user.username} to: '{user.email}'")
    
except User.DoesNotExist:
    print(f"❌ User '{username}' not found.")
except Exception as e:
    print(f"❌ Error updating user: {e}")
