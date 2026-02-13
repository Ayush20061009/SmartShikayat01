from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.db import IntegrityError  # Import IntegrityError
from .forms import CitizenSignUpForm, OfficerSignUpForm
from django.views.generic import TemplateView
from notifications.utils import send_welcome_email

def home(request):
    return render(request, 'home.html')

def citizen_signup(request):
    if request.method == 'POST':
        form = CitizenSignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                # Wrap email sending to prevent crashing if email fails
                try:
                    send_welcome_email(user)
                except Exception:
                    pass 
                return redirect('complaint_list')
            except IntegrityError:
                form.add_error('username', 'This username is already taken. Please choose another.')
    else:
        form = CitizenSignUpForm()
    return render(request, 'registration/citizen_signup.html', {'form': form})

def officer_signup(request):
    if request.method == 'POST':
        form = OfficerSignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                try:
                    send_welcome_email(user)
                except Exception:
                    pass
                return redirect('officer_dashboard')
            except IntegrityError:
                # This catches the specific error you are seeing
                form.add_error('username', 'This username is already taken. Please choose another.')
    else:
        form = OfficerSignUpForm()
    return render(request, 'registration/officer_signup.html', {'form': form})

def dashboard(request):
    if request.user.role == 'citizen':
        return redirect('complaint_list')
    elif request.user.role == 'officer':
        return redirect('officer_dashboard')
    else:
        return redirect('admin:index')