from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Notification


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "notifications/notification_list.html", {"notifications": notifications})


@login_required
def notification_delete(request, pk):
    get_object_or_404(Notification, pk=pk, user=request.user).delete()
    return redirect("notifications:notification_list")
