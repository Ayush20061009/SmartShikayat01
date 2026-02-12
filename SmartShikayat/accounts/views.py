from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CitizenSignUpForm, OfficerSignUpForm
from django.views.generic import TemplateView

def home(request):
    return render(request, 'home.html')

def citizen_signup(request):
    if request.method == 'POST':
        form = CitizenSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('complaint_list')
    else:
        form = CitizenSignUpForm()
    return render(request, 'registration/citizen_signup.html', {'form': form})

def officer_signup(request):
    if request.method == 'POST':
        form = OfficerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('officer_dashboard')
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
