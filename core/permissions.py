from functools import wraps

from django.core.exceptions import PermissionDenied


def role_requis(*roles):
    """Réserve une vue à certains rôles : @role_requis('super_admin', 'admin')."""
    def decorateur(vue):
        @wraps(vue)
        def enveloppe(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return vue(request, *args, **kwargs)
        return enveloppe
    return decorateur


super_admin_requis = role_requis('super_admin')
admin_requis = role_requis('super_admin', 'admin')
