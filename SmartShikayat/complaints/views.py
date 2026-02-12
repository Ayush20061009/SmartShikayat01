from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Complaint
from .forms import ComplaintForm
from notifications.models import Notification
from django.core.mail import send_mail, EmailMultiAlternatives
from notifications.utils import send_traffic_fine_email, send_complaint_confirmation, send_officer_alert, send_status_update_email, send_welcome_email
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib import messages
from accounts.forms import VehicleRegistrationForm
from django.db.models import Count, F, Window
import logging

# Configure logging to file
logger = logging.getLogger('complaint_debug')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('complaint_debug.log')
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

import qrcode
from io import BytesIO
from email.mime.image import MIMEImage
from .utils_ai import check_image_ai, extract_license_plate, check_illegal_parking_ai, check_garbage_issue_ai, check_road_damage_ai

User = get_user_model()

def send_fine_email(request, complaint):
    """
    Helper function to generate QR code and send fine email to vehicle owner.
    Returns (success, message).
    """
    try:
        final_plate = complaint.vehicle_number
        if not final_plate:
             return False, "No vehicle number associated with this complaint."

        owner = User.objects.get(vehicle_number=final_plate)
        fine_amt = complaint.fine_amount

        # Generate QR Code
        payment_link = request.build_absolute_uri(f"/complaints/pay_fine/{complaint.tracking_id}/")
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(payment_link)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_image_data = buffer.getvalue()
        
        # Email Content
        subject = f"Traffic Violation Fine - {final_plate}"
        text_content = f"You have been fined Rs. {fine_amt} for illegal parking. Pay here: {payment_link}"
        
        from django.utils import timezone
        email_date = complaint.created_at or timezone.now()
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9; }}
                .header {{ background-color: #d9534f; color: white; padding: 15px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 20px; background-color: white; border-radius: 0 0 10px 10px; }}
                .details {{ background-color: #f1f1f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #d9534f; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .footer {{ margin-top: 20px; font-size: 12px; text-align: center; color: #777; }}
                .evidence-img {{ max-width: 100%; border-radius: 5px; margin-top: 10px; border: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin:0;">Traffic Violation Notice</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>{owner.username}</strong>,</p>
                    <p>This is an official notification regarding a traffic violation involving your vehicle.</p>
                    
                    <div class="details">
                        <table style="width:100%">
                            <tr><td><strong>Violation:</strong></td><td>Illegal Parking</td></tr>
                            <tr><td><strong>Vehicle Number:</strong></td><td>{final_plate}</td></tr>
                            <tr><td><strong>Location:</strong></td><td>{complaint.location}</td></tr>
                            <tr><td><strong>Fine Amount:</strong></td><td><strong>Rs. {fine_amt}</strong></td></tr>
                            <tr><td><strong>Date:</strong></td><td>{email_date.strftime('%Y-%m-%d %H:%M')}</td></tr>
                        </table>
                    </div>

                    <p><strong>Description:</strong> {complaint.description}</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{payment_link}" class="btn">Pay Fine Now</a>
                    </div>
                    
                    <p style="text-align: center;">Scan to Pay:</p>
                    <div style="text-align: center;">
                        <img src="cid:qrcode_image" alt="Payment QR Code" width="150" height="150" style="border: 1px solid #ccc; padding: 5px;">
                    </div>

                    <p style="text-align: center; font-size: 0.9em; margin-top: 20px;">
                        <em>Photographic evidence is attached below.</em>
                    </p>
                     <div style="text-align: center;">
                        <img src="cid:evidence_image" alt="Evidence" class="evidence-img">
                    </div>
                </div>
                <div class="footer">
                    <p>Smart City Traffic Control | Automated System</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [owner.email])
        msg.attach_alternative(html_content, "text/html")
        
        # Attach QR Code
        image = MIMEImage(qr_image_data)
        image.add_header('Content-ID', '<qrcode_image>')
        msg.attach(image)

        # Attach Evidence Image
        if complaint.image:
             try:
                # Read image data properly depending on storage
                complaint.image.open()
                evidence_data = complaint.image.read()
                evidence_img = MIMEImage(evidence_data)
                evidence_img.add_header('Content-ID', '<evidence_image>')
                msg.attach(evidence_img)
                complaint.image.close() # Good practice
             except Exception as img_err:
                 print(f"Error attaching evidence image: {img_err}")

        
        msg.send()
        
        # Notify Owner
        Notification.objects.create(
            user=owner,
            message=f"You have been fined Rs. {fine_amt} for illegal parking. Pay here: {payment_link}"
        )
        
        return True, f"Email sent to {owner.email}"

    except User.DoesNotExist:
        return False, f"Vehicle '{final_plate}' not found in database."
    except Exception as e:
        return False, f"Email sending failed: {str(e)}"

@login_required
def complaint_list(request):
    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'complaints/complaint_list.html', {'complaints': complaints})

@login_required
def complaint_create(request):
    if request.method == 'POST':
        logger.info("Complaint Create POST received")
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            logger.info("Form is Valid. Processing...")
            # Initial save to get instance but not db commit if we need to check AI/Validation
            complaint = form.save(commit=False)
            complaint.user = request.user
            
            # Log state before logic branch
            logger.info(f"Complaint Category: '{complaint.category}', Image Details: {complaint.image}")

            # --- AI Check & Traffic Violation Logic ---
            if complaint.category == 'parking':
                if not complaint.image:
                     logger.warning("Parking complaint submitted without image. Blocking.")
                     form.add_error('image', "Evidence Image is REQUIRED for Illegal Parking complaints.")
                     return render(request, 'complaints/complaint_create.html', {'form': form})
                
                try:
                    logger.info("Starting AI Logic...")

                    
                    # 0. Check Manual vs AI Plate Match (Feature Request)
                    manual_plate = form.cleaned_data.get('manual_vehicle_number')
                    logger.info(f"Manual Plate Input: {manual_plate}")
                    
                    # 1. AI Image Detection (AI Generated?)
                    is_ai, ai_msg = check_image_ai(complaint.image)
                    logger.info(f"AI Generated Check: {is_ai} ({ai_msg})")

                    if is_ai:
                        logger.warning(f"Image rejected as AI generated: {ai_msg}")
                        form.add_error('image', f"Image rejected: Detected as AI-generated ({ai_msg})")
                        return render(request, 'complaints/complaint_create.html', {'form': form})
                    
                    complaint.is_ai_checked = True
                    
                    # 2. Check Illegal Parking (AI)
                    is_illegal, illegal_reason = check_illegal_parking_ai(complaint.image)
                    logger.info(f"Illegal Parking Check: {is_illegal} ({illegal_reason})")
                    if not is_illegal:
                        logger.warning(f"AI: Might not be illegal parking: {illegal_reason}")

                    # 3. Extract Plate
                    ai_plate_number = extract_license_plate(complaint.image)
                    logger.info(f"Extracted Plate: {ai_plate_number}")
                    
                    final_plate = None
                    
                    if manual_plate and ai_plate_number:
                        norm_manual = manual_plate.replace(" ", "").upper()
                        norm_ai = ai_plate_number.replace(" ", "").upper()
                        
                        if norm_manual != norm_ai and norm_manual not in norm_ai:
                             logger.warning(f"Mismatch - Manual: {norm_manual}, AI: {norm_ai}")
                             form.add_error('manual_vehicle_number', f"Mismatch: Manual entry '{manual_plate}' does not match AI detected plate '{ai_plate_number}'.")
                             return render(request, 'complaints/complaint_create.html', {'form': form})
                        final_plate = norm_manual
                        logger.info(f"Plate Matched/Confirmed: {final_plate}")
                        
                    elif ai_plate_number:
                        final_plate = ai_plate_number
                        logger.info(f"Using AI Plate: {final_plate}")
                    elif manual_plate:
                         logger.warning("AI Could not detect plate, using manual input.")
                         final_plate = manual_plate.replace(" ", "").upper()
                    else:
                        logger.error("No plate detected (AI failed + No Manual). Blocking.")
                        form.add_error('image', "Could not detect a license plate. Please provide a clearer image or enter the vehicle number manually.")
                        return render(request, 'complaints/complaint_create.html', {'form': form})

                    logger.info(f"Final Plate for Fine: {final_plate}")
                    complaint.vehicle_number = final_plate
                    
                    try:
                        owner = User.objects.get(vehicle_number=final_plate)
                        logger.info(f"Owner Found: {owner.username} ({owner.email})")
                        
                        # 5. Calculate Fine
                        fine_amt = 100
                        if 'city' in complaint.location.lower():
                            fine_amt = 200
                        
                        complaint.fine_amount = fine_amt
                        
                        # 6. Generate QR Code & Send Email
                        complaint.save() # Save to populate created_at for email
                        logger.info("Calling send_fine_email...")
                        success, msg = send_fine_email(request, complaint)
                        logger.info(f"Email Result: {success} - {msg}")
                        if not success:
                            if "Vehicle" in msg and "not found" in msg:
                                form.add_error(None, msg)
                                return render(request, 'complaints/complaint_create.html', {'form': form})
                            else:
                                logger.error(f"Email Warning: {msg}")
                                messages.warning(request, f"Complaint created but email failed: {msg}")
                        
                        if success:
                            # Show Masked Email Notification
                            try:
                                email_parts = owner.email.split('@')
                                if len(email_parts) == 2:
                                    masked = f"{email_parts[0][:2]}****@{email_parts[1]}"
                                    messages.success(request, f"Fine notification sent to owner: {masked}")
                            except:
                                pass # formatting error

                    except User.DoesNotExist:
                        logger.warning(f"Owner Not Found for {final_plate}")
                        form.add_error(None, f"Vehicle '{final_plate}' not found in our database. Cannot process fine.")
                        return render(request, 'complaints/complaint_create.html', {'form': form})
                            
                except Exception as e:
                    print(f"AI/Email Process Error: {e}")
                    form.add_error(None, f"System Verification Error: {str(e)}")
                    return render(request, 'complaints/complaint_create.html', {'form': form})
            
            # --- End AI Logic ---
            
            # --- Garbage Validation Logic ---
            if complaint.category == 'garbage':
                if complaint.image:
                    try:
                        logger.info("Starting Garbage AI Validation...")
                        
                        # Check if image is AI-generated
                        is_ai, ai_msg = check_image_ai(complaint.image)
                        logger.info(f"AI Generated Check: {is_ai} ({ai_msg})")
                        
                        if is_ai:
                            logger.warning(f"Image rejected as AI generated: {ai_msg}")
                            form.add_error('image', f"Image rejected: Detected as AI-generated ({ai_msg})")
                            return render(request, 'complaints/complaint_create.html', {'form': form})
                        
                        complaint.is_ai_checked = True
                        
                        # Check if image shows garbage issues
                        is_valid_garbage, garbage_reason = check_garbage_issue_ai(complaint.image)
                        logger.info(f"Garbage Validation: {is_valid_garbage} ({garbage_reason})")
                        
                        if not is_valid_garbage:
                            logger.warning(f"Image doesn't show garbage issues: {garbage_reason}")
                            form.add_error('image', f"Image validation failed: The image doesn't appear to show garbage-related issues (trash overflow, dirty bins, etc.). AI says: {garbage_reason}")
                            return render(request, 'complaints/complaint_create.html', {'form': form})
                        
                        logger.info("Garbage image validated successfully")
                        
                    except Exception as e:
                        logger.error(f"Garbage AI Validation Error: {e}")
                        # Don't block the complaint if AI validation fails
                        print(f"Garbage AI Validation Error: {e}")
            
            # --- End Garbage Validation ---
            
            # --- Road Damage Validation Logic ---
            if complaint.category == 'road':
                if complaint.image:
                    try:
                        logger.info("Starting Road Damage AI Validation...")
                        
                        # Check if image is AI-generated
                        is_ai, ai_msg = check_image_ai(complaint.image)
                        logger.info(f"AI Generated Check: {is_ai} ({ai_msg})")
                        
                        if is_ai:
                            logger.warning(f"Image rejected as AI generated: {ai_msg}")
                            form.add_error('image', f"Image rejected: Detected as AI-generated ({ai_msg})")
                            return render(request, 'complaints/complaint_create.html', {'form': form})
                        
                        complaint.is_ai_checked = True
                        
                        # Check if image shows road damage
                        is_valid_damage, damage_reason = check_road_damage_ai(complaint.image)
                        logger.info(f"Road Damage Validation: {is_valid_damage} ({damage_reason})")
                        
                        if not is_valid_damage:
                            logger.warning(f"Image doesn't show road damage: {damage_reason}")
                            form.add_error('image', f"Image validation failed: The image doesn't appear to show road damage (potholes, cracks, bad road). AI says: {damage_reason}")
                            return render(request, 'complaints/complaint_create.html', {'form': form})
                        
                        logger.info("Road damage image validated successfully")
                        
                    except Exception as e:
                        logger.error(f"Road Damage AI Validation Error: {e}")
                        # Don't block the complaint if AI validation fails
                        print(f"Road Damage AI Validation Error: {e}")
            
            # --- End Road Damage Validation ---


            complaint.save() # Finally save to DB
            
            # 1. Notify the User (Citizen) - Reporter
            Notification.objects.create(
                user=request.user,
                message=f"Your complaint regarding '{complaint.get_category_display()}' has been submitted successfully. Tracking ID: {complaint.tracking_id}"
            )
            
            # Send Confirmation Email
            send_complaint_confirmation(request.user, complaint)

            # (Old logic for parking - removed or integrated above, but let's keep other notifications)
            
            # 3. Notify Relevant Officers (Universal Logic)
            if complaint.department:
                officers = User.objects.filter(role='officer', department=complaint.department)
                for officer in officers:
                    # Filter by area if officer has one
                    if officer.area and officer.area.lower() not in complaint.location.lower():
                        continue
                        
                    Notification.objects.create(
                        user=officer,
                        message=f"New Complaint Alert: A {complaint.get_category_display()} issue has been reported at {complaint.location}. Please investigate."
                    )
                    
                    # Send Officer Alert Email
                    send_officer_alert(officer, complaint)
            
            return redirect('complaint_list')
        else:
             logger.error(f"Form Validation Failed: {form.errors}")
             messages.error(request, 'Please correct the errors below.')
    else:
        form = ComplaintForm()
    return render(request, 'complaints/complaint_create.html', {
        'form': form, 
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    })

@login_required
def officer_dashboard(request):
    if request.user.role != 'officer':
        return redirect('complaint_list')
    
    # Filter complaints by the officer's department
    # Note: user.department should match complaint.department (or be mapped)
    # The models use 'department' field on both.
    
    complaints = Complaint.objects.filter(department=request.user.department)
    
    # Location-based restriction
    if request.user.area:
        complaints = complaints.filter(location__icontains=request.user.area)
        
    # Prioritize Frequent Locations (Hotspots)
    # Sort by frequency of location specific to this view's filter, then by date
    complaints = complaints.annotate(
        loc_freq=Window(
            expression=Count('id'),
            partition_by=[F('location')]
        )
    ).order_by('-loc_freq', '-created_at')
        
    return render(request, 'complaints/officer_dashboard.html', {'complaints': complaints})

@login_required
def complaint_update_status(request, tracking_id):
    if request.user.role != 'officer':
        return redirect('complaint_list')
        
    complaint = get_object_or_404(Complaint, tracking_id=tracking_id)
    
    # Verify officer belongs to the same department
    if complaint.department != request.user.department:
         return redirect('officer_dashboard')

    # Location-based restriction
    if request.user.area and request.user.area.lower() not in complaint.location.lower():
         return redirect('officer_dashboard')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Complaint.STATUS_CHOICES):
            complaint.status = new_status
            complaint.save()
            
            # Send Status Update Email
            send_status_update_email(complaint.user, complaint)
            
    return redirect('officer_dashboard')

@login_required
def department_leaderboard(request):
    if request.user.role != 'officer':
        return redirect('complaint_list')
        
    # Get complaints for the officer's department
    # Prioritize Frequent Locations (Hotspots)
    complaints = Complaint.objects.filter(department=request.user.department)
    
    complaints = complaints.annotate(
        loc_freq=Window(
            expression=Count('id'),
            partition_by=[F('location')]
        )
    ).order_by('-loc_freq', '-created_at')
    
    return render(request, 'complaints/leaderboard.html', {'complaints': complaints})

@login_required
def pay_fine(request, tracking_id):
    """
    Simulates the payment of a fine by the vehicle owner.
    """
    complaint = get_object_or_404(Complaint, tracking_id=tracking_id)
    
    if complaint.fine_paid:
        return render(request, 'complaints/payment_success.html', {'complaint': complaint, 'already_paid': True})
        
    if request.method == 'POST':
        # Process Payment
        complaint.fine_paid = True
        complaint.status = 'resolved' # Auto-resolve upon payment
        complaint.save()
        
        # Reward the Reporter (30%)
        # Reporter is complaint.user
        reporter = complaint.user
        reward = complaint.fine_amount * 0.30
        from decimal import Decimal
        # Ensure decimal precision handled
        reporter.wallet_balance += Decimal(reward)
        reporter.save()
        
        complaint.reporter_earning = Decimal(reward)
        complaint.save()
        
        # Notify Reporter
        Notification.objects.create(
            user=reporter,
            message=f"Reward Credited! You earned Rs. {reward} from a successful parking fine payment. Total Balance: {reporter.wallet_balance}"
        )
        
        return render(request, 'complaints/payment_success.html', {'complaint': complaint, 'success': True})
    
    return render(request, 'complaints/pay_ticket.html', {'complaint': complaint})

@login_required
def user_earnings(request):
    """
    Shows the user's earnings from reporting parking violations.
    """
    # Only show if user has complaints offering earnings
    earning_complaints = Complaint.objects.filter(user=request.user, reporter_earning__gt=0).order_by('-created_at')
    
    return render(request, 'complaints/earnings.html', {
        'earning_complaints': earning_complaints,
        'wallet_balance': request.user.wallet_balance
    })

@login_required
def register_vehicle_owner(request):
    """
    View for officers to register a vehicle owner.
    """
    if request.user.role != 'officer':
        return redirect('complaint_list')
        
    if request.method == 'POST':
        form = VehicleRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                # Set a default password
                user.set_password("SmartCity@123")
                user.save()
                
                # Send Welcome Email
                send_welcome_email(user)
                
                # Success message
                messages.success(request, f"Vehicle Owner {user.username} registered successfully with vehicle {user.vehicle_number}.")
                return redirect('officer_dashboard')
            except Exception as e:
                form.add_error(None, f"Error creating user: {e}")
    else:
        form = VehicleRegistrationForm()
        
    return render(request, 'complaints/register_vehicle.html', {'form': form})

@login_required
def withdraw_earnings(request):
    """
    Simulates withdrawing earnings.
    """
    if request.method == 'POST':
        if request.user.wallet_balance > 0:
            amount = request.user.wallet_balance
            # Simulate Bank Transfer
            request.user.wallet_balance = 0
            request.user.save()
            
            messages.success(request, f"Withdrawal of Rs. {amount} successful! Amount transferred to your bank account.")
            
            Notification.objects.create(
                user=request.user,
                message=f"Withdrawal of Rs. {amount} processed successfully."
            )
        else:
             messages.error(request, "Insufficient balance to withdraw.")
             
    return redirect('user_earnings')
@login_required
def resend_fine_email(request, tracking_id):
    """
    Manually resend the fine email to the vehicle owner.
    """
    if request.user.role != 'officer':
        return redirect('complaint_list')
        
    complaint = get_object_or_404(Complaint, tracking_id=tracking_id)
    
    if complaint.category != 'parking' or not complaint.vehicle_number:
         messages.error(request, "This complaint is not eligible for a fine email.")
         return redirect('officer_dashboard')

    success, msg = send_fine_email(request, complaint)
    
    if success:
        # Show Masked Email
        masked_msg = msg
        try:
             # msg from send_fine_email might be "Email sent successfully"
             # helper function for masking would be better, but inline is fast
             owner = User.objects.get(vehicle_number=complaint.vehicle_number)
             email_parts = owner.email.split('@')
             if len(email_parts) == 2:
                  masked = f"{email_parts[0][:2]}****@{email_parts[1]}"
                  masked_msg = f"Email re-sent to: {masked}"
        except:
             pass
        messages.success(request, masked_msg)
    else:
        messages.error(request, msg)
        
    return redirect('officer_dashboard')
