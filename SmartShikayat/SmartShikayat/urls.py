from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/citizen/', account_views.citizen_signup, name='citizen_signup'),
    path('accounts/signup/officer/', account_views.officer_signup, name='officer_signup'),
    path('complaints/', include('complaints.urls')),
    path('notifications/', include('notifications.urls')),
    path('dashboard/', account_views.dashboard, name='dashboard'),
    path('', account_views.home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
