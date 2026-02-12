from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CitizenSignUpForm(UserCreationForm):
    phone = forms.CharField(max_length=15, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('phone',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'citizen'
        user.save()
        return user

class OfficerSignUpForm(UserCreationForm):
    department = forms.ChoiceField(choices=User.DEPARTMENT_CHOICES, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('department', 'area',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'officer'
        user.save()
        return user

class VehicleRegistrationForm(forms.ModelForm):
    # Form for Officers to register vehicle owners
    username = forms.CharField(max_length=150, help_text="Create a username for the vehicle owner")
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'vehicle_number']
        
    def save(self, commit=True):
        # We manually create user with set_password in the view usually, 
        # or override save here. Let's keep it simple and just return instance if commit=False
        user = super().save(commit=False)
        user.role = 'citizen' # Default role for vehicle owners
        if commit:
            user.save()
        return user
