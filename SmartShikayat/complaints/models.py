import uuid
from django.db import models
from django.conf import settings

class Complaint(models.Model):

    CATEGORY_CHOICES = [
        ('road', 'Road Damage'),
        ('water', 'Water Issues'),
        ('garbage', 'Garbage'),
        ('parking', 'Illegal Parking'),
        ('fire', 'Fire Hazard'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    DEPARTMENT_CHOICES = [
        ('municipal', 'Municipal Corporation'),
        ('water', 'Water Department'),
        ('traffic', 'Traffic Police'),
        ('fire', 'Fire Department'),
    ]

    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='complaints'
    )

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='complaints/', null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
    # Fields for Parking Violations
    vehicle_number = models.CharField(max_length=20, blank=True, null=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fine_paid = models.BooleanField(default=False)
    reporter_earning = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_ai_checked = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.department:
            if self.category in ['road', 'garbage']:
                self.department = 'municipal'
            elif self.category == 'water':
                self.department = 'water'
            elif self.category == 'parking':
                self.department = 'traffic'
            elif self.category == 'fire':
                self.department = 'fire'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracking_id} - {self.status}"
