
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def notifications_view(request):
    notes = Notification.objects.filter(user=request.user)
    return render(request, 'notifications.html', {'notifications': notes})
