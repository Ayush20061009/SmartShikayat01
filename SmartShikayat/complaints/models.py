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
    
    # AI Validation Fields
    ai_confidence_score = models.FloatField(null=True, blank=True, help_text="AI confidence score (0-100)")
    ai_validation_result = models.TextField(blank=True, help_text="AI validation response")
    ai_validation_passed = models.BooleanField(null=True, blank=True, help_text="Whether AI validation passed")
    ai_language = models.CharField(max_length=10, default='en', help_text="Language used for AI validation")

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


class AIValidationMetrics(models.Model):
    """
    Tracks AI validation performance metrics over time
    """
    complaint = models.OneToOneField(
        Complaint,
        on_delete=models.CASCADE,
        related_name='ai_metrics'
    )
    
    # Validation Details
    validation_type = models.CharField(max_length=20, help_text="Type: parking, road, garbage")
    ai_detected = models.BooleanField(help_text="What AI detected (True=issue found)")
    ai_confidence = models.FloatField(help_text="Confidence score 0-100")
    ai_response = models.TextField(help_text="Full AI response text")
    
    # Performance Tracking
    processing_time_ms = models.IntegerField(null=True, blank=True, help_text="AI processing time in milliseconds")
    api_model_used = models.CharField(max_length=50, default="llama-3.2-11b-vision-preview")
    
    # User Feedback (for accuracy tracking)
    user_agreed = models.BooleanField(null=True, blank=True, help_text="Did user agree with AI assessment?")
    user_feedback_text = models.TextField(blank=True, help_text="User's feedback on AI accuracy")
    
    # Officer Verification (ground truth)
    officer_verified = models.BooleanField(null=True, blank=True, help_text="Officer's verification of complaint")
    officer_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "AI Validation Metric"
        verbose_name_plural = "AI Validation Metrics"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"AI Metrics for {self.complaint.tracking_id}"
    
    @property
    def accuracy_status(self):
        """Returns accuracy status based on officer verification"""
        if self.officer_verified is None:
            return "Pending Verification"
        elif self.officer_verified == self.ai_detected:
            return "Accurate"
        else:
            return "Inaccurate"


class AIFeedback(models.Model):
    """
    User feedback on AI validation accuracy
    """
    FEEDBACK_CHOICES = [
        ('correct', 'AI was correct'),
        ('incorrect', 'AI was incorrect'),
        ('unsure', 'Not sure'),
    ]
    
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='ai_feedbacks'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_feedbacks'
    )
    
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_CHOICES)
    comments = models.TextField(blank=True, help_text="Additional user comments")
    
    # What AI said vs what user thinks
    ai_said_valid = models.BooleanField(help_text="What AI concluded")
    user_thinks_valid = models.BooleanField(help_text="What user actually thinks")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "AI Feedback"
        verbose_name_plural = "AI Feedbacks"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.feedback_type} - {self.complaint.tracking_id}"

