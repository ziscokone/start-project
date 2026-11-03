from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponseServerError


def hub(request):
    """Page d'accueil : une tuile par module accessible."""
    return render(request, 'core/hub.html')


def erreur_403(request, exception=None):
    return render(request, 'core/erreur.html', {
        'code': 403,
        'titre': 'Accès refusé',
        'texte': "Vous n'avez pas les droits pour ouvrir cette page.",
        'icone': 'bi-shield-lock',
    }, status=403)


@login_not_required
def erreur_404(request, exception=None):
    return render(request, 'core/erreur.html', {
        'code': 404,
        'titre': 'Page introuvable',
        'texte': "Cette page n'existe pas ou a été déplacée.",
        'icone': 'bi-signpost-split',
    }, status=404)


@login_not_required
def erreur_500(request):
    # Gabarit autonome : aucune requête en base, rien qui puisse échouer à nouveau.
    return HttpResponseServerError(loader.get_template('core/500.html').render())
