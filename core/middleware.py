from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from core import modules


class AccesModuleMiddleware:
    """Refuse l'accès aux pages d'un module si l'utilisateur n'y a pas droit."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        if not match or not request.user.is_authenticated:
            return None
        module = modules.module_pour_namespace(match.namespace)
        if module and module not in modules.modules_pour(request.user):
            raise PermissionDenied("Vous n'avez pas accès à ce module.")
        return None


class ChangementMotDePasseMiddleware:
    """Oblige à changer le mot de passe quand un administrateur l'a réinitialisé."""

    PAGES_LIBRES = {'compte:mot_de_passe', 'compte:deconnexion',
                    'pwa_manifeste', 'pwa_sw', 'pwa_icone', 'pwa_hors_ligne'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user
        if not user.is_authenticated or not getattr(user, 'doit_changer_mot_de_passe', False):
            return None
        match = request.resolver_match
        if match and match.view_name in self.PAGES_LIBRES:
            return None
        messages.warning(request, "Choisissez un nouveau mot de passe pour continuer.")
        return redirect('compte:mot_de_passe')
