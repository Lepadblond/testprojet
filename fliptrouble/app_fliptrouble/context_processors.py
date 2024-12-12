from .models import Notification

def navbar_context_processor(request):
    if request.user.is_authenticated:
        notifications_non_lues = Notification.objects.filter(to_user=request.user, is_read=False)
    else:
        notifications_non_lues = []
    return {'notifications_non_lues': notifications_non_lues}
