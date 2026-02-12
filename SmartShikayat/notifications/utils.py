
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import qrcode
from io import BytesIO
from email.mime.image import MIMEImage

def send_traffic_fine_email(user, complaint, fine_amount, payment_link, violation_reason):
    """
    Sends a traffic fine email with QR code to the vehicle owner.
    """
    # Explicitly reload user from DB
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(pk=user.pk)
    except User.DoesNotExist:
        print("❌ User not found in DB")
        return False

    # Print detailed info to console
    print("\n" + "=" * 80)
    print("📧 SENDING TRAFFIC FINE EMAIL")
    print("=" * 80)
    print(f"Recipient (from DB): {user.username}")
    print(f"Email Address: {user.email}")
    print(f"Vehicle Number: {complaint.vehicle_number}")
    
    if not user.email:
        print("❌ ABORTING: User has no email address configured in the database.")
        print("=" * 80 + "\n")
        return False
    print(f"Fine Amount: Rs. {fine_amount}")
    print(f"Location: {complaint.location}")
    print(f"Violation Reason: {violation_reason}")
    print(f"Payment Link: {payment_link}")
    print("-" * 80)
    
    subject = f"Traffic Violation Fine - {complaint.vehicle_number}"
    
    # Generate QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(payment_link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_image_data = buffer.getvalue()

    # Email Context
    context = {
        'user': user,
        'complaint': complaint,
        'fine_amount': fine_amount,
        'payment_link': payment_link,
        'element_id': 'qrcode_image', # generic ID, but valid for CID
        'reason': violation_reason
    }

    # We can use a template or raw string. For now, raw string to keep it simple as before, 
    # but using a variable for cleaner code. 
    # Ideally we should use render_to_string with a template, but let's stick to the inline style 
    # or a simple constructed HTML to avoid creating new template files if not necessary yet.
    # Actually, let's create a robust HTML body here.

    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
                .header {{ background-color: #f8f9fa; padding: 10px; border-bottom: 1px solid #ddd; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ font-size: 12px; color: #777; text-align: center; margin-top: 20px; }}
                .button {{ background-color: #d9534f; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Traffic Violation Notice</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>{user.username}</strong>,</p>
                    <p>You have been issued a fine for illegal parking at {complaint.location}.</p>
                    <p><strong>Reason:</strong> {violation_reason}</p>
                    <ul>
                        <li><strong>Vehicle:</strong> {complaint.vehicle_number}</li>
                        <li><strong>Date:</strong> {complaint.created_at.strftime('%Y-%m-%d %H:%M')}</li>
                        <li><strong>Fine Amount:</strong> Rs. {fine_amount}</li>
                    </ul>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{payment_link}" class="button">Pay Fine Now</a>
                    </p>
                    <p style="text-align: center;">
                        <img src="cid:qrcode_image" alt="Payment QR Code" width="200" height="200">
                    </p>
                </div>
                <div class="footer">
                    <p>SmartShikayat - Smart City Initiative</p>
                    <p>This is an automated message. Please do not reply.</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    text_content = strip_tags(html_content)
    
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    
    image = MIMEImage(qr_image_data)
    image.add_header('Content-ID', '<qrcode_image>')
    msg.attach(image)
    
    try:
        msg.send()
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print("=" * 80 + "\n")
        return True
    except Exception as e:
        print(f"❌ FAILED TO SEND EMAIL: {e}")
        print("=" * 80 + "\n")
        return False

def send_complaint_confirmation(user, complaint):
    """
    Sends a confirmation email to the user (reporter) when a complaint is submitted.
    """
    # Explicitly reload user from DB to ensure we have the latest email
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(pk=user.pk)
    except User.DoesNotExist:
        print("❌ User not found in DB")
        return False

    print("\n" + "=" * 80)
    print("📧 SENDING COMPLAINT CONFIRMATION EMAIL")
    print("=" * 80)
    print(f"Recipient (from DB): {user.username}")
    print(f"Email Address: {user.email}")
    print(f"Complaint Type: {complaint.get_category_display()}")
    print(f"Tracking ID: {complaint.tracking_id}")
    print("-" * 80)
    
    if not user.email:
        print("❌ ABORTING: User has no email address configured in the database.")
        print("=" * 80 + "\n")
        return False

    subject = f"Complaint Submitted - ID #{str(complaint.tracking_id)[:8]}"
    
    html_content = f"""
    <html>
        <body>
            <h2>Complaint Received</h2>
            <p>Dear {user.username},</p>
            <p>Your complaint regarding <strong>{complaint.get_category_display()}</strong> has been submitted successfully.</p>
            <p><strong>Tracking ID:</strong> {complaint.tracking_id}</p>
            <p><strong>Status:</strong> {complaint.get_status_display()}</p>
            <p>We will notify you once an officer reviews your complaint.</p>
            <p>Thank you for being a responsible citizen.</p>
        </body>
    </html>
    """
    text_content = strip_tags(html_content)
    
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print("=" * 80 + "\n")
        return True
    except Exception as e:
        print(f"❌ FAILED TO SEND EMAIL: {e}")
        print("=" * 80 + "\n")
        return False

def send_officer_alert(officer, complaint):
    """
    Sends an alert to the officer about a new complaint.
    """
    # Explicitly reload user from DB
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        officer = User.objects.get(pk=officer.pk)
    except User.DoesNotExist:
        print("❌ Officer not found in DB")
        return False

    print("\n" + "=" * 80)
    print("📧 SENDING OFFICER ALERT EMAIL")
    print("=" * 80)
    print(f"Recipient (from DB): {officer.username}")
    print(f"Email Address: {officer.email}")
    print(f"Department: {officer.department}")
    
    if not officer.email:
        print("❌ ABORTING: Officer has no email address configured in the database.")
        print("=" * 80 + "\n")
        return False
    print(f"Complaint Type: {complaint.get_category_display()}")
    print(f"Location: {complaint.location}")
    print("-" * 80)
    
    subject = f"New Complaint Assigned - {complaint.get_category_display()}"
    
    html_content = f"""
    <html>
        <body>
            <h2>New Complaint Alert</h2>
            <p>Officer {officer.username},</p>
            <p>A new complaint has been filed in your department/area.</p>
            <ul>
                <li><strong>Category:</strong> {complaint.get_category_display()}</li>
                <li><strong>Location:</strong> {complaint.location}</li>
                <li><strong>Description:</strong> {complaint.description}</li>
            </ul>
            <p>Please login to your dashboard to review and take action.</p>
        </body>
    </html>
    """
    text_content = strip_tags(html_content)
    
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [officer.email])
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print("=" * 80 + "\n")
        return True
    except Exception as e:
        print(f"❌ FAILED TO SEND EMAIL: {e}")
        print("=" * 80 + "\n")
        return False

def send_status_update_email(user, complaint):
    """
    Sends an email to the user when the status of their complaint changes.
    """
    # Explicitly reload user from DB
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(pk=user.pk)
    except User.DoesNotExist:
        print("❌ User not found in DB")
        return False

    print("\n" + "=" * 80)
    print("📧 SENDING STATUS UPDATE EMAIL")
    print("=" * 80)
    print(f"Recipient (from DB): {user.username}")
    print(f"Email Address: {user.email}")
    print(f"Complaint ID: {complaint.tracking_id}")
    
    if not user.email:
        print("❌ ABORTING: User has no email address configured in the database.")
        print("=" * 80 + "\n")
        return False
    print(f"New Status: {complaint.get_status_display()}")
    print("-" * 80)
    
    subject = f"Complaint Status Updated - {complaint.get_status_display()}"
    
    html_content = f"""
    <html>
        <body>
            <h2>Status Update</h2>
            <p>Dear {user.username},</p>
            <p>The status of your complaint (ID: {complaint.tracking_id}) has been updated.</p>
            <ul>
                <li><strong>Category:</strong> {complaint.get_category_display()}</li>
                <li><strong>New Status:</strong> {complaint.get_status_display()}</li>
            </ul>
            <p>You can view more details in your dashboard.</p>
            <p>Thank you for using SmartShikayat.</p>
        </body>
    </html>
    """
    text_content = strip_tags(html_content)
    
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print("=" * 80 + "\n")
        return True
    except Exception as e:
        print(f"❌ FAILED TO SEND EMAIL: {e}")
        print("=" * 80 + "\n")
        return False

def send_welcome_email(user):
    """
    Sends a welcome email to the newly registered user.
    """
    # Explicitly reload user from DB
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(pk=user.pk)
    except User.DoesNotExist:
        print("❌ User not found in DB")
        return False

    print("\n" + "=" * 80)
    print("📧 SENDING WELCOME EMAIL")
    print("=" * 80)
    print(f"Recipient (from DB): {user.username}")
    print(f"Email Address: {user.email}")
    print(f"Role: {user.role}")
    
    if not user.email:
        print("❌ ABORTING: User has no email address configured in the database.")
        print("=" * 80 + "\n")
        return False
    print("-" * 80)
    
    subject = "Welcome to SmartShikayat!"
    
    html_content = f"""
    <html>
        <body>
            <h2>Welcome, {user.username}!</h2>
            <p>Thank you for registering on SmartShikayat - Your Smart Civic Companion.</p>
            <p>You can now:</p>
            <ul>
                <li>File complaints about civic issues.</li>
                <li>Track the status of your complaints.</li>
                <li> contribute to a better city.</li>
            </ul>
            <p>We are glad to have you on board.</p>
        </body>
    </html>
    """
    text_content = strip_tags(html_content)
    
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send()
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print("=" * 80 + "\n")
        return True
    except Exception as e:
        print(f"❌ FAILED TO SEND EMAIL: {e}")
        print("=" * 80 + "\n")
        return False
