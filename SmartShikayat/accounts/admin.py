from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'department', 'area')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'department', 'area')}),
    )
    list_display = ['username', 'email', 'role', 'department', 'area', 'is_staff']
    list_filter = ['role', 'department', 'area', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'phone']

admin.site.register(User, CustomUserAdmin)
