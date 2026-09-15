from django.db.models import Q
from django.utils import timezone
from .models import Announcement

def active_announcements(request):
    now=timezone.now()
    qs=Announcement.objects.filter(is_active=True).filter(Q(starts_at__isnull=True)|Q(starts_at__lte=now)).filter(Q(ends_at__isnull=True)|Q(ends_at__gte=now))
    if request.user.is_authenticated and request.user.school_name:
        qs=qs.filter(Q(school_name="")|Q(school_name__iexact=request.user.school_name))
    else:
        qs=qs.filter(school_name="")
    return {"active_announcements":qs[:3]}
