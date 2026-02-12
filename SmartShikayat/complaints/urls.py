from django.urls import path
from . import views
from . import ajax_views

urlpatterns = [
    path('my-complaints/', views.complaint_list, name='complaint_list'),
    path('create/', views.complaint_create, name='complaint_create'),
    path('officer/dashboard/', views.officer_dashboard, name='officer_dashboard'),
    path('update/<uuid:tracking_id>/', views.complaint_update_status, name='complaint_update_status'),
    path('leaderboard/', views.department_leaderboard, name='department_leaderboard'),
    path('pay_fine/<uuid:tracking_id>/', views.pay_fine, name='pay_fine'),
    path('my-earnings/', views.user_earnings, name='user_earnings'),
    path('withdraw/', views.withdraw_earnings, name='withdraw_earnings'),
    path('officer/register-vehicle/', views.register_vehicle_owner, name='register_vehicle_owner'),
    path('officer/update/<uuid:tracking_id>/', views.complaint_update_status, name='complaint_update_status'),
    path('ajax/extract-plate/', ajax_views.extract_plate_ajax, name='extract_plate_ajax'),
]
