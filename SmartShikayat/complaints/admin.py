from django.contrib import admin
from .models import Complaint, AIValidationMetrics, AIFeedback

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('tracking_id', 'user', 'category', 'status', 'department', 'ai_confidence_score', 'ai_validation_passed', 'created_at')
    list_filter = ('status', 'category', 'department', 'ai_validation_passed', 'is_ai_checked')
    search_fields = ('tracking_id', 'user__username', 'location', 'description')
    readonly_fields = ('tracking_id', 'created_at', 'ai_confidence_score', 'ai_validation_result')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tracking_id', 'user', 'category', 'status', 'department')
        }),
        ('Complaint Details', {
            'fields': ('description', 'location', 'image', 'created_at')
        }),
        ('AI Validation', {
            'fields': ('is_ai_checked', 'ai_confidence_score', 'ai_validation_result', 'ai_validation_passed', 'ai_language'),
            'classes': ('collapse',)
        }),
        ('Parking Violation Details', {
            'fields': ('vehicle_number', 'fine_amount', 'fine_paid', 'reporter_earning'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AIValidationMetrics)
class AIValidationMetricsAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'validation_type', 'ai_detected', 'ai_confidence', 'accuracy_status', 'processing_time_ms', 'created_at')
    list_filter = ('validation_type', 'ai_detected', 'user_agreed', 'officer_verified')
    search_fields = ('complaint__tracking_id', 'ai_response')
    readonly_fields = ('created_at', 'updated_at', 'accuracy_status')
    
    fieldsets = (
        ('Complaint Reference', {
            'fields': ('complaint',)
        }),
        ('AI Analysis', {
            'fields': ('validation_type', 'ai_detected', 'ai_confidence', 'ai_response', 'processing_time_ms', 'api_model_used')
        }),
        ('Feedback & Verification', {
            'fields': ('user_agreed', 'user_feedback_text', 'officer_verified', 'officer_notes', 'accuracy_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AIFeedback)
class AIFeedbackAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'user', 'feedback_type', 'ai_said_valid', 'user_thinks_valid', 'created_at')
    list_filter = ('feedback_type', 'ai_said_valid', 'user_thinks_valid')
    search_fields = ('complaint__tracking_id', 'user__username', 'comments')
    readonly_fields = ('created_at',)
