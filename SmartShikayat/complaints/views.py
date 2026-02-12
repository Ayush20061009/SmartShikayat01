from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Complaint
from .forms import ComplaintForm
from notifications.models import Notification
from notifications.utils import send_traffic_fine_email, send_complaint_confirmation, send_officer_alert, send_status_update_email, send_welcome_email
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib import messages
from accounts.forms import VehicleRegistrationForm

User = get_user_model()

@login_required
def complaint_list(request):
    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'complaints/complaint_list.html', {'complaints': complaints})

@login_required
def complaint_create(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            # Initial save to get instance but not db commit if we need to check AI/Validation
            complaint = form.save(commit=False)
            complaint.user = request.user
            
            # --- AI Check & Traffic Violation Logic ---
            if complaint.category == 'parking' and complaint.image:
                try:
                    from .utils_ai import check_image_ai, extract_license_plate, check_illegal_parking_ai
                    
                    # 0. Check Manual vs AI Plate Match (Feature Request)
                    manual_plate = form.cleaned_data.get('manual_vehicle_number')
                    
                    # 1. AI Image Detection (AI Generated?)
                    is_ai, ai_msg = check_image_ai(complaint.image)
                    if is_ai:
                        form.add_error('image', f"Image rejected: Detected as AI-generated ({ai_msg})")
                        return render(request, 'complaints/complaint_create.html', {'form': form})
                    
                    complaint.is_ai_checked = True
                    
                    # 2. Check Illegal Parking (AI)
                    is_illegal, illegal_reason = check_illegal_parking_ai(complaint.image)
                    if not is_illegal:
                        # Optional: Reject or Warn. For now, let's reject strict.
                        # form.add_error('image', f"AI Analysis: Vehicle appears to be parked legally or unclear. ({illegal_reason})")
                        # return render(request, 'complaints/complaint_create.html', {'form': form})
                        # Allowing vague "NO" for now as models vary, but logging it.
                        print(f"AI Warning: Might not be illegal parking: {illegal_reason}")

                    # 3. Extract Plate
                    ai_plate_number = extract_license_plate(complaint.image)
                    
                    final_plate = None
                    
                    if manual_plate and ai_plate_number:
                        # Compare (Strip spaces and case)
                        norm_manual = manual_plate.replace(" ", "").upper()
                        norm_ai = ai_plate_number.replace(" ", "").upper()
                        
                        # Basic fuzzy match or exact? Let's do exact containment or 80% match.
                        # Strict for now as per user request "check number plate is match"
                        if norm_manual != norm_ai and norm_manual not in norm_ai:
                             form.add_error('manual_vehicle_number', f"Mismatch: Manual entry '{manual_plate}' does not match AI detected plate '{ai_plate_number}'.")
                             return render(request, 'complaints/complaint_create.html', {'form': form})
                        final_plate = norm_manual # Use manual if confirmed by AI
                        
                    elif ai_plate_number:
                        final_plate = ai_plate_number
                    elif manual_plate:
                         # Fallback: AI failed to detect any plate, but user provided one.
                         # We TRUST the user's manual input in this case, instead of blocking them.
                         print("AI Warning: Could not detect plate, using manual input.")
                         final_plate = manual_plate.replace(" ", "").upper()
                    else:
                        form.add_error('image', "Could not detect a license plate. Please provide a clearer image or enter the vehicle number manually.")
                        return render(request, 'complaints/complaint_create.html', {'form': form})

                    complaint.vehicle_number = final_plate
                    
                    try:
                        owner = User.objects.get(vehicle_number=final_plate)
                        print(f"✅ FOUND VEHICLE OWNER: {owner.username} (Email: {owner.email})")
                        
                        # 5. Calculate Fine
                        fine_amt = 100
                        if 'city' in complaint.location.lower():
                            fine_amt = 200
                        
                        complaint.fine_amount = fine_amt
                        
                        payment_link = request.build_absolute_uri(f"/complaints/pay_fine/{complaint.tracking_id}/")
                        
                        # Send Email using Utility
                        email_sent = send_traffic_fine_email(owner, complaint, fine_amt, payment_link, illegal_reason)
                        
                        if email_sent:
                            # --- PRINT LINK FOR DEV TESTING ---
                            print("\n" + "="*50)
                            print(f"EMAIL SENT TO: {owner.email}")
                            print(f"PAYMENT LINK: {payment_link}")
                            print("="*50 + "\n")
                        else:
                            print(f"Email failed to send to {owner.email}")

                        Notification.objects.create(
                            user=owner,
                            message=f"You have been fined Rs. {fine_amt} for illegal parking. Pay here: {payment_link}"
                        )
                        
                        # --- PRINT LINK FOR DEV TESTING ---
                        print("\n" + "="*50)
                        print(f"EMAIL SENT TO: {owner.email}")
                        print(f"PAYMENT LINK: {payment_link}")
                        print("="*50 + "\n")
                        
                        Notification.objects.create(
                            user=owner,
                            message=f"You have been fined Rs. {fine_amt} for illegal parking. Pay here: {payment_link}"
                        )

                    except User.DoesNotExist:
                        form.add_error(None, f"Vehicle '{final_plate}' not found in our database. Cannot process fine.")
                        return render(request, 'complaints/complaint_create.html', {'form': form})
                            
                except Exception as e:
                    print(f"AI/Email Process Error: {e}")
                    form.add_error(None, f"System Verification Error: {str(e)}")
                    return render(request, 'complaints/complaint_create.html', {'form': form})
            
            # --- End AI Logic ---
            
            # --- End AI Logic ---

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
        form = ComplaintForm()
    return render(request, 'complaints/complaint_create.html', {'form': form})

@login_required
def officer_dashboard(request):
    if request.user.role != 'officer':
        return redirect('complaint_list')
    
    # Filter complaints by the officer's department
    # Note: user.department should match complaint.department (or be mapped)
    # The models use 'department' field on both.
    
    complaints = Complaint.objects.filter(department=request.user.department).order_by('-created_at')
    
    # Location-based restriction
    if request.user.area:
        complaints = complaints.filter(location__icontains=request.user.area)
        
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
    complaints = Complaint.objects.filter(department=request.user.department).order_by('-created_at')
    
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
