"""
Registre des modules affichés sur le hub.

Chaque application déclare son module dans un fichier `module.py` (chargé
automatiquement au démarrage). Exemple : apps/comptes/module.py.

    enregistrer(DefinitionModule(
        cle='stock',                      # identifiant unique, utilisé pour les droits
        nom='Stock',
        description='Articles, entrées et sorties',
        icone='bi-box-seam',              # icône Bootstrap Icons
        couleur='orange',                 # marine, bleu, vert, violet, orange, rouge, turquoise
        url_name='stock:accueil',         # page ouverte depuis le hub
        namespaces=('stock',),            # namespaces d'URL qui appartiennent au module
        menu=(
            Section('Pilotage', (
                Lien('Tableau de bord', 'stock:accueil', 'bi-speedometer2'),
            )),
        ),
    ))

Tout le reste est automatique : la tuile du hub, le menu vertical, le contrôle
d'accès (une page d'un namespace du module est refusée à qui n'a pas le droit),
et l'entrée dans la liste des droits utilisateurs.
"""
from dataclasses import dataclass
from typing import Callable, Optional

from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch, reverse

COULEURS = ('marine', 'bleu', 'vert', 'violet', 'orange', 'rouge', 'turquoise')


@dataclass(frozen=True)
class Lien:
    """Un lien du menu vertical."""
    titre: str
    url_name: Optional[str] = None          # None : lien grisé avec le badge « bientôt »
    icone: str = 'bi-dot'
    actif_sur: tuple = ()                   # autres pages (url_name) qui allument ce lien
    badge: Optional[Callable] = None        # fonction(request) -> nombre ou texte (None/0 : rien)
    visible: Optional[Callable] = None      # fonction(user) -> bool (None : toujours visible)


@dataclass(frozen=True)
class Section:
    """Un groupe de liens, avec un petit titre en majuscules."""
    titre: str
    liens: tuple


@dataclass(frozen=True)
class DefinitionModule:
    cle: str
    nom: str
    url_name: str
    namespaces: tuple
    description: str = ''
    icone: str = 'bi-grid'
    couleur: str = 'marine'
    ordre: int = 100
    menu: tuple = ()
    recherche_url: Optional[str] = None     # page qui reçoit ?q= depuis la barre de recherche
    notifications: Optional[Callable] = None  # fonction(request) -> liste de dict


_registre: dict[str, DefinitionModule] = {}


def enregistrer(module: DefinitionModule) -> DefinitionModule:
    if module.cle in _registre:
        raise ImproperlyConfigured(f"Le module « {module.cle} » est déjà enregistré.")
    if module.couleur not in COULEURS:
        raise ImproperlyConfigured(f"Couleur inconnue pour « {module.cle} » : {module.couleur}.")
    _registre[module.cle] = module
    return module


def tous() -> list[DefinitionModule]:
    return sorted(_registre.values(), key=lambda m: (m.ordre, m.nom))


def get(cle: str) -> Optional[DefinitionModule]:
    return _registre.get(cle)


def module_pour_namespace(namespace: str) -> Optional[DefinitionModule]:
    if not namespace:
        return None
    racine = namespace.split(':')[0]
    for module in _registre.values():
        if racine in module.namespaces:
            return module
    return None


def modules_pour(user) -> list[DefinitionModule]:
    """Modules actifs auxquels l'utilisateur a accès, dans l'ordre du hub."""
    if not user.is_authenticated:
        return []
    cache = getattr(user, '_cache_modules', None)
    if cache is not None:
        return cache

    from apps.comptes.models import Module

    actifs = set(Module.objects.filter(actif=True).values_list('cle', flat=True))
    if user.est_admin:
        autorises = actifs
    else:
        autorises = set(user.modules_autorises.filter(actif=True).values_list('cle', flat=True))
    resultat = [m for m in tous() if m.cle in autorises]
    user._cache_modules = resultat
    return resultat


def construire_menu(module: DefinitionModule, request) -> list[dict]:
    """Prépare le menu vertical : liens visibles, lien actif, badges."""
    match = request.resolver_match
    page = f'{match.namespace}:{match.url_name}' if match and match.namespace else ''
    sections = []
    for section in module.menu:
        liens = []
        for lien in section.liens:
            if lien.visible and not lien.visible(request.user):
                continue
            url = None
            if lien.url_name:
                try:
                    url = reverse(lien.url_name)
                except NoReverseMatch:
                    url = None
            liens.append({
                'titre': lien.titre,
                'icone': lien.icone,
                'url': url,
                'actif': bool(lien.url_name) and (page == lien.url_name or page in lien.actif_sur),
                'badge': lien.badge(request) if (lien.badge and url) else None,
            })
        if liens:
            sections.append({'titre': section.titre, 'liens': liens})
    return sections
