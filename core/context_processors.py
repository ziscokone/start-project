from core import modules


def interface(request):
    """Variables disponibles dans tous les gabarits."""
    from apps.etablissement.models import Etablissement

    contexte = {'etablissement': Etablissement.charger()}

    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return contexte

    accessibles = modules.modules_pour(user)
    match = getattr(request, 'resolver_match', None)
    module_actif = modules.module_pour_namespace(match.namespace) if match else None
    if module_actif not in accessibles:
        module_actif = None

    notifications = []
    for module in accessibles:
        if module.notifications:
            notifications.extend(module.notifications(request))

    contexte.update({
        'modules_accessibles': accessibles,
        'module_actif': module_actif,
        'menu_module': modules.construire_menu(module_actif, request) if module_actif else [],
        'notifications': notifications,
    })
    return contexte
