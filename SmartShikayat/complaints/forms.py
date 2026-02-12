from django import forms
from .models import Complaint

class ComplaintForm(forms.ModelForm):
    manual_vehicle_number = forms.CharField(
        max_length=20, 
        required=False, 
        label="Manual Vehicle Number (Optional)",
        help_text="If visible, please enter the vehicle number."
    )
    
    class Meta:
        model = Complaint
        fields = ['category', 'description', 'location', 'image', 'manual_vehicle_number']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }