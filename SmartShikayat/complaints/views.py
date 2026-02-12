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
            # AI validation for complaints with images
            if complaint.image:
                try:
                    from .utils_ai import check_image_ai, extract_license_plate, check_illegal_parking_ai, check_road_damage_ai, check_garbage_issue_ai
                    from .models import AIValidationMetrics
                    
                    # Get user language preference (default to English)
                    user_lang = getattr(request.user, 'preferred_language', 'en') or 'en'
                    
                    # 1. Check if image is AI-generated (applies to all categories)
                    is_ai, ai_msg, ai_conf, ai_time = check_image_ai(complaint.image, language=user_lang)
                    if is_ai:
                        form.add_error('image', f"❌ Image rejected: Detected as AI-generated ({ai_msg}). Please upload a real photograph.")
                        return render(request, 'complaints/complaint_create.html', {'form': form})
                    
                    complaint.is_ai_checked = True
                    complaint.ai_language = user_lang
                    
                    # 2. Category-specific AI validation
                    if complaint.category == 'parking':
                        # Parking-specific validation
                        manual_plate = form.cleaned_data.get('manual_vehicle_number')
                        
                        # Check if parking is actually illegal
                        is_illegal, illegal_reason, parking_conf, parking_time = check_illegal_parking_ai(complaint.image, language=user_lang)
                        
                        # Store AI metrics
                        complaint.ai_confidence_score = parking_conf
                        complaint.ai_validation_result = illegal_reason
                        complaint.ai_validation_passed = is_illegal
                        
                        if not is_illegal:
                            messages.warning(request, f"⚠️ AI Analysis: {illegal_reason}. Please verify this is actually illegal parking before submitting.")
                            # Allow user to proceed but with warning
                        else:
                            messages.success(request, f"✅ AI Verification: {illegal_reason}. Your complaint appears valid.")
                        
                        # Extract license plate
                        ai_plate_number, plate_conf, plate_time = extract_license_plate(complaint.image, language=user_lang)
                        
                        final_plate = None
                        
                        if manual_plate and ai_plate_number:
                            # Compare plates
                            norm_manual = manual_plate.replace(" ", "").upper()
                            norm_ai = ai_plate_number.replace(" ", "").upper()
                            
                            if norm_manual != norm_ai and norm_manual not in norm_ai:
                                form.add_error('manual_vehicle_number', f"❌ Mismatch: Manual entry '{manual_plate}' does not match AI detected plate '{ai_plate_number}'.")
                                return render(request, 'complaints/complaint_create.html', {'form': form})
                            final_plate = norm_manual
                            
                        elif ai_plate_number:
                            final_plate = ai_plate_number
                        elif manual_plate:
                            print("AI Warning: Could not detect plate, using manual input.")
                            final_plate = manual_plate.replace(" ", "").upper()
                        else:
                            form.add_error('image', "❌ Could not detect a license plate. Please provide a clearer image or enter the vehicle number manually.")
                            return render(request, 'complaints/complaint_create.html', {'form': form})

                        complaint.vehicle_number = final_plate
                        complaint.save()  # Save to get ID for metrics
                        
                        # Create AI metrics record
                        AIValidationMetrics.objects.create(
                            complaint=complaint,
                            validation_type='parking',
                            ai_detected=is_illegal,
                            ai_confidence=parking_conf,
                            ai_response=illegal_reason,
                            processing_time_ms=parking_time
                        )
                        
                        # Find vehicle owner and process fine
                        try:
                            owner = User.objects.get(vehicle_number=final_plate)
                            print(f"✅ FOUND VEHICLE OWNER: {owner.username} (Email: {owner.email})")
                            
                            # Calculate fine
                            fine_amt = 100
                            if 'city' in complaint.location.lower():
                                fine_amt = 200
                            
                            complaint.fine_amount = fine_amt
                            
                            payment_link = request.build_absolute_uri(f"/complaints/pay_fine/{complaint.tracking_id}/")
                            
                            # Send email
                            email_sent = send_traffic_fine_email(owner, complaint, fine_amt, payment_link, illegal_reason)
                            
                            if email_sent:
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

                        except User.DoesNotExist:
                            form.add_error(None, f"❌ Vehicle '{final_plate}' not found in our database. Cannot process fine.")
                            return render(request, 'complaints/complaint_create.html', {'form': form})
                    
                    elif complaint.category == 'road':
                        # Road damage validation
                        is_damaged, damage_reason, road_conf, road_time = check_road_damage_ai(complaint.image, language=user_lang)
                        
                        # Store AI metrics
                        complaint.ai_confidence_score = road_conf
                        complaint.ai_validation_result = damage_reason
                        complaint.ai_validation_passed = is_damaged
                        
                        # STRICT VALIDATION: Reject if no road damage detected
                        if not is_damaged:
                            form.add_error('image', f"❌ AI Validation Failed: {damage_reason}. Please upload an image showing clear road damage (potholes, cracks, broken pavement, etc.).")
                            return render(request, 'complaints/complaint_create.html', {'form': form})
                        
                        # Save and create metrics only if validation passed
                        complaint.save()  # Save to get ID
                        
                        # Create AI metrics record
                        AIValidationMetrics.objects.create(
                            complaint=complaint,
                            validation_type='road',
                            ai_detected=is_damaged,
                            ai_confidence=road_conf,
                            ai_response=damage_reason,
                            processing_time_ms=road_time
                        )
                        
                        messages.success(request, f"✅ AI Verification: {damage_reason}. Your road damage complaint appears valid.")
                    
                    elif complaint.category == 'garbage':
                        # Garbage issue validation
                        is_garbage_issue, garbage_reason, garbage_conf, garbage_time = check_garbage_issue_ai(complaint.image, language=user_lang)
                        
                        # Store AI metrics
                        complaint.ai_confidence_score = garbage_conf
                        complaint.ai_validation_result = garbage_reason
                        complaint.ai_validation_passed = is_garbage_issue
                        
                        # STRICT VALIDATION: Reject if no garbage issue detected
                        if not is_garbage_issue:
                            form.add_error('image', f"❌ AI Validation Failed: {garbage_reason}. Please upload an image showing clear garbage accumulation, littering, or waste issues.")
                            return render(request, 'complaints/complaint_create.html', {'form': form})
                        
                        # Save and create metrics only if validation passed
                        complaint.save()  # Save to get ID
                        
                        # Create AI metrics record
                        AIValidationMetrics.objects.create(
                            complaint=complaint,
                            validation_type='garbage',
                            ai_detected=is_garbage_issue,
                            ai_confidence=garbage_conf,
                            ai_response=garbage_reason,
                            processing_time_ms=garbage_time
                        )
                        
                        messages.success(request, f"✅ AI Verification: {garbage_reason}. Your garbage complaint appears valid.")
                            
                except Exception as e:
                    print(f"AI/Email Process Error: {e}")
                    form.add_error(None, f"❌ System Verification Error: {str(e)}")
                    return render(request, 'complaints/complaint_create.html', {'form': form})
            
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
