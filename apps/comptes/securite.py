"""Comptes bloqués par django-axes après trop d'échecs de connexion."""
from datetime import timedelta

from axes.models import AccessAttempt
from django.conf import settings
from django.utils import timezone


def comptes_bloques():
    qs = AccessAttempt.objects.filter(failures_since_start__gte=settings.AXES_FAILURE_LIMIT)
    duree = getattr(settings, 'AXES_COOLOFF_TIME', None)
    if isinstance(duree, (int, float)):
        qs = qs.filter(attempt_time__gte=timezone.now() - timedelta(hours=duree))
    return qs.order_by('-attempt_time')
