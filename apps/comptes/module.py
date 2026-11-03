"""Déclaration du module « Gestion utilisateurs » (tuile du hub + menu vertical)."""
from django.urls import reverse

from core.modules import DefinitionModule, Lien, Section, enregistrer


def _nb_actifs(request):
    from .models import Utilisateur
    return Utilisateur.objects.filter(is_active=True).count()


def _nb_bloques(request):
    from .securite import comptes_bloques
    return comptes_bloques().count() or None


def _est_super_admin(user):
    return user.est_super_admin


def _notifications(request):
    from .models import Role, Utilisateur
    from .securite import comptes_bloques

    resultat = []
    bloques = comptes_bloques().count()
    if bloques:
        resultat.append({
            'icone': 'bi-shield-lock',
            'niveau': 'danger',
            'texte': f"{bloques} compte{'s' if bloques > 1 else ''} bloqué{'s' if bloques > 1 else ''} "
                     "après des échecs de connexion",
            'url': reverse('comptes:bloques'),
        })
    sans_module = Utilisateur.objects.filter(
        is_active=True, role=Role.UTILISATEUR, modules_autorises__isnull=True).count()
    if sans_module:
        resultat.append({
            'icone': 'bi-grid-3x3-gap',
            'niveau': 'alerte',
            'texte': f"{sans_module} utilisateur{'s' if sans_module > 1 else ''} sans aucun module",
            'url': reverse('comptes:droits'),
        })
    return resultat


enregistrer(DefinitionModule(
    cle='utilisateurs',
    nom='Gestion utilisateurs',
    description='Comptes, rôles et droits d’accès',
    icone='bi-people-fill',
    couleur='violet',
    ordre=900,
    url_name='comptes:accueil',
    namespaces=('comptes', 'etablissement'),
    recherche_url='comptes:utilisateur_list',
    notifications=_notifications,
    menu=(
        Section('Pilotage', (
            Lien('Tableau de bord', 'comptes:accueil', 'bi-speedometer2'),
        )),
        Section('Utilisateurs', (
            Lien('Tous les utilisateurs', 'comptes:utilisateur_list', 'bi-people',
                 actif_sur=('comptes:utilisateur_update', 'comptes:utilisateur_password',
                            'comptes:utilisateur_delete'),
                 badge=_nb_actifs),
            Lien('Nouvel utilisateur', 'comptes:utilisateur_create', 'bi-person-plus'),
            Lien("Droits d'accès", 'comptes:droits', 'bi-grid-3x3-gap'),
        )),
        Section('Sécurité', (
            Lien('Journal de connexion', 'comptes:journal', 'bi-clock-history'),
            Lien('Comptes bloqués', 'comptes:bloques', 'bi-shield-lock', badge=_nb_bloques),
        )),
        Section('Configuration', (
            Lien('Établissement', 'etablissement:parametres', 'bi-building-gear',
                 visible=_est_super_admin),
        )),
    ),
))
