"""Vues du module « Gestion utilisateurs »."""
from axes.models import AccessAttempt, AccessFailureLog, AccessLog
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.permissions import admin_requis

from .forms import (CreationUtilisateurForm, ReinitialisationForm, UtilisateurForm,
                    dernier_super_admin, modules_attribuables)
from .models import DESCRIPTION_ROLES, Role, Utilisateur
from .securite import comptes_bloques

PAR_PAGE = 20


def _roles_aide(acteur):
    return [(libelle, DESCRIPTION_ROLES[valeur]) for valeur, libelle in acteur.roles_attribuables()]


def _cible_gerable(request, pk):
    cible = get_object_or_404(Utilisateur, pk=pk)
    if not request.user.peut_gerer(cible):
        raise PermissionDenied("Vous ne pouvez pas modifier ce compte.")
    return cible


# ── Tableau de bord ──────────────────────────────────────────────────────

def accueil(request):
    utilisateurs = Utilisateur.objects.all()
    stats = utilisateurs.aggregate(
        total=Count('id'),
        actifs=Count('id', filter=Q(is_active=True)),
        inactifs=Count('id', filter=Q(is_active=False)),
    )
    nb_bloques = comptes_bloques().count()

    a_traiter = []
    sans_module = utilisateurs.filter(is_active=True, role=Role.UTILISATEUR, modules_autorises__isnull=True)
    if sans_module.exists():
        a_traiter.append({
            'icone': 'bi-grid-3x3-gap', 'nombre': sans_module.count(),
            'titre': "Attribuer des modules",
            'texte': "Ces comptes ne voient aucune tuile sur le hub.",
            'url': 'comptes:droits', 'action': "Attribuer",
        })
    if nb_bloques:
        a_traiter.append({
            'icone': 'bi-shield-lock', 'nombre': nb_bloques,
            'titre': "Débloquer des comptes",
            'texte': "Trop d'échecs de connexion. Vérifiez avant de débloquer.",
            'url': 'comptes:bloques', 'action': "Voir",
        })
    jamais = utilisateurs.filter(is_active=True, last_login__isnull=True).count()
    if jamais:
        a_traiter.append({
            'icone': 'bi-person-exclamation', 'nombre': jamais,
            'titre': "Comptes jamais utilisés",
            'texte': "Transmettez les identifiants ou désactivez les comptes inutiles.",
            'url': 'comptes:utilisateur_list', 'filtre': '?statut=jamais', 'action': "Voir",
        })

    return render(request, 'comptes/accueil.html', {
        'stats': stats,
        'nb_bloques': nb_bloques,
        'a_traiter': a_traiter,
        'derniers_crees': utilisateurs.order_by('-date_joined')[:5],
        'dernieres_connexions': utilisateurs.filter(last_login__isnull=False).order_by('-last_login')[:6],
        'repartition': [
            {'valeur': v, 'libelle': l, 'nombre': utilisateurs.filter(role=v).count()}
            for v, l in Role.choices
        ],
    })


# ── Liste et fiches ──────────────────────────────────────────────────────

def utilisateur_list(request):
    qs = Utilisateur.objects.prefetch_related('modules_autorises')
    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    statut = request.GET.get('statut', '')

    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
                       | Q(email__icontains=q) | Q(telephone__icontains=q) | Q(poste__icontains=q))
    if role in Role.values:
        qs = qs.filter(role=role)
    if statut == 'actif':
        qs = qs.filter(is_active=True)
    elif statut == 'inactif':
        qs = qs.filter(is_active=False)
    elif statut == 'jamais':
        qs = qs.filter(last_login__isnull=True)

    page = Paginator(qs, PAR_PAGE).get_page(request.GET.get('page'))
    return render(request, 'comptes/utilisateur_list.html', {
        'page': page, 'q': q, 'role': role, 'statut': statut,
        'roles': Role.choices, 'filtre_actif': bool(q or role or statut),
    })


def utilisateur_create(request):
    form = CreationUtilisateurForm(request.POST or None, request.FILES or None, acteur=request.user)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Compte de {user.nom_affiche} créé.")
            return redirect('comptes:utilisateur_list')
        messages.error(request, "Vérifiez les champs signalés.")
    return render(request, 'comptes/utilisateur_form.html', {
        'form': form, 'creation': True, 'roles_aide': _roles_aide(request.user)})


def utilisateur_update(request, pk):
    cible = _cible_gerable(request, pk)
    form = UtilisateurForm(request.POST or None, request.FILES or None, instance=cible, acteur=request.user)
    if request.method == 'POST':
        if form.is_valid():
            if request.POST.get('retirer_photo') and not request.FILES.get('photo'):
                form.instance.photo.delete(save=False)
                form.instance.photo = None
            form.save()
            messages.success(request, f"Fiche de {cible.nom_affiche} enregistrée.")
            return redirect('comptes:utilisateur_list')
        messages.error(request, "Vérifiez les champs signalés.")
    return render(request, 'comptes/utilisateur_form.html', {
        'form': form, 'cible': cible, 'creation': False, 'roles_aide': _roles_aide(request.user)})


@require_POST
def utilisateur_toggle(request, pk):
    cible = _cible_gerable(request, pk)
    if cible.pk == request.user.pk:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
    elif cible.is_active and cible.est_super_admin and dernier_super_admin(cible):
        messages.error(request, "Il doit toujours rester au moins un Super Admin actif.")
    else:
        cible.is_active = not cible.is_active
        cible.save(update_fields=['is_active'])
        etat = "activé" if cible.is_active else "désactivé"
        messages.success(request, f"Compte de {cible.nom_affiche} {etat}.")
    return redirect(request.POST.get('suivant') or 'comptes:utilisateur_list')


def utilisateur_password(request, pk):
    cible = _cible_gerable(request, pk)
    if cible.pk == request.user.pk:
        return redirect('compte:mot_de_passe')
    form = ReinitialisationForm(cible, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"Mot de passe de {cible.nom_affiche} réinitialisé.")
        return redirect('comptes:utilisateur_list')
    return render(request, 'comptes/utilisateur_password.html', {'form': form, 'cible': cible})


@admin_requis
def utilisateur_delete(request, pk):
    cible = _cible_gerable(request, pk)
    if cible.pk == request.user.pk:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('comptes:utilisateur_list')
    if cible.est_super_admin and dernier_super_admin(cible):
        messages.error(request, "Il doit toujours rester au moins un Super Admin actif.")
        return redirect('comptes:utilisateur_list')
    if request.method == 'POST':
        nom = cible.nom_affiche
        cible.delete()
        messages.success(request, f"Compte de {nom} supprimé.")
        return redirect('comptes:utilisateur_list')
    return render(request, 'comptes/utilisateur_confirm_delete.html', {'cible': cible})


# ── Droits d'accès (grille utilisateurs × modules) ───────────────────────

def droits(request):
    modules = list(modules_attribuables(request.user))
    cibles = (Utilisateur.objects.filter(is_active=True, role=Role.UTILISATEUR)
              .exclude(pk=request.user.pk).prefetch_related('modules_autorises'))
    cibles = [c for c in cibles if request.user.peut_gerer(c)]

    if request.method == 'POST':
        ids_portee = {m.pk for m in modules}
        for cible in cibles:
            coches = {int(v) for v in request.POST.getlist(f'u{cible.pk}') if v.isdigit()} & ids_portee
            hors_portee = {m.pk for m in cible.modules_autorises.all() if m.pk not in ids_portee}
            cible.modules_autorises.set(coches | hors_portee)
        messages.success(request, "Droits d'accès enregistrés.")
        return redirect('comptes:droits')

    lignes = []
    for cible in cibles:
        actuels = {m.pk for m in cible.modules_autorises.all()}
        lignes.append({'user': cible, 'cases': [(m, m.pk in actuels) for m in modules]})
    admins = Utilisateur.objects.filter(is_active=True, role__in=[Role.SUPER_ADMIN, Role.ADMIN])
    return render(request, 'comptes/droits.html', {
        'modules': modules, 'lignes': lignes, 'admins': admins})


# ── Sécurité ─────────────────────────────────────────────────────────────

def journal(request):
    onglet = 'echecs' if request.GET.get('onglet') == 'echecs' else 'connexions'
    if onglet == 'echecs':
        qs = AccessFailureLog.objects.order_by('-attempt_time')
    else:
        qs = AccessLog.objects.order_by('-attempt_time')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(ip_address__icontains=q))
    page = Paginator(qs, 10).get_page(request.GET.get('page'))
    return render(request, 'comptes/journal.html', {
        'page': page, 'onglet': onglet, 'q': q,
        'nb_echecs': AccessFailureLog.objects.count()})


def bloques(request):
    if request.method == 'POST':
        tentative = get_object_or_404(AccessAttempt, pk=request.POST.get('tentative'))
        nom = tentative.username or tentative.ip_address
        tentative.delete()
        messages.success(request, f"Compte « {nom} » débloqué.")
        return redirect('comptes:bloques')
    return render(request, 'comptes/bloques.html', {'tentatives': comptes_bloques()})
