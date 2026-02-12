
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    ROLE_CHOICES = [
        ('citizen', 'Citizen'),
        ('officer', 'Officer'),
    ]

    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    DEPARTMENT_CHOICES = [
        ('municipal', 'Municipal'),
        ('water', 'Water Department'),
        ('traffic', 'Traffic Police'),
        ('fire', 'Fire Department'),
    ]

    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        blank=True,
        null=True
    )
    area = models.CharField(max_length=100, blank=True, null=True, help_text="Officer's jurisdiction area (e.g., 'Ahmedabad')")
    vehicle_number = models.CharField(max_length=20, blank=True, null=True, unique=True, help_text="Vehicle License Plate Number")
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.username
