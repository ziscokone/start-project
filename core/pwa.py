"""Application installable (PWA) : manifeste, service worker, icônes, page hors ligne.

Tout est construit à partir de la fiche Établissement (nom, sigle, logo) :
un nouveau projet devient installable sans rien configurer.

Après une mise à jour importante du CSS/JS, augmentez PWA_VERSION dans
config/settings.py : les anciens fichiers en cache seront supprimés.
"""
import io
import json
import unicodedata

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from PIL import Image, ImageDraw, ImageFont

from apps.etablissement.models import Etablissement

COULEUR_THEME = '#1e3260'   # marine : barre du téléphone, fond de l'écran de démarrage
COULEUR_ICONE = '#E67E22'   # orange : fond de l'icône quand il n'y a pas de logo
TAILLES = (180, 192, 512)   # 180 : iPhone/iPad ; 192 et 512 : Android, ordinateur
POLICES = (                 # première police grasse trouvée sur le serveur
    'DejaVuSans-Bold.ttf', 'LiberationSans-Bold.ttf', 'Arial Bold.ttf', 'arialbd.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
)


def _police(taille):
    """Police grasse du système ; sinon police intégrée (sans accents)."""
    for nom in POLICES:
        try:
            return ImageFont.truetype(nom, taille), True
        except OSError:
            continue
    return ImageFont.load_default(size=taille), False


def _sans_accents(texte):
    return unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode()


def version():
    """Change quand le code (PWA_VERSION) ou la fiche établissement change."""
    etab = Etablissement.charger()
    return f"{getattr(settings, 'PWA_VERSION', '1')}-{int(etab.date_modification.timestamp())}"


@login_not_required
@require_GET
@cache_control(max_age=3600)
def manifeste(request):
    etab = Etablissement.charger()
    v = version()
    donnees = {
        'id': '/',
        'name': etab.nom,
        'short_name': etab.nom_court,
        'description': etab.slogan or etab.description or etab.nom,
        'lang': 'fr',
        'start_url': reverse('hub'),
        'scope': '/',
        'display': 'standalone',
        'orientation': 'any',
        'background_color': COULEUR_THEME,
        'theme_color': COULEUR_THEME,
        'icons': [
            {'src': f"{reverse('pwa_icone', args=[t])}?v={v}", 'sizes': f'{t}x{t}',
             'type': 'image/png', 'purpose': 'any'}
            for t in (192, 512)
        ] + [
            {'src': f"{reverse('pwa_icone', args=[512])}?v={v}&masque=1", 'sizes': '512x512',
             'type': 'image/png', 'purpose': 'maskable'},
        ],
    }
    return HttpResponse(json.dumps(donnees, ensure_ascii=False), content_type='application/manifest+json')


@login_not_required
@require_GET
@cache_control(max_age=60 * 60 * 24 * 30)
def icone(request, taille):
    """Icône carrée : le logo sur fond blanc, ou les initiales sur fond orange."""
    if taille not in TAILLES:
        raise Http404
    masque = request.GET.get('masque') == '1'   # Android découpe l'icône (rond, goutte…) : on garde une marge
    etab = Etablissement.charger()

    logo = None
    if etab.logo:
        try:
            logo = Image.open(etab.logo).convert('RGBA')
        except (OSError, ValueError):
            logo = None

    if logo:
        image = Image.new('RGBA', (taille, taille), '#ffffff')
        cote = int(taille * (0.62 if masque else 0.8))
        logo.thumbnail((cote, cote), Image.LANCZOS)
        image.alpha_composite(logo, ((taille - logo.width) // 2, (taille - logo.height) // 2))
    else:
        image = Image.new('RGBA', (taille, taille), COULEUR_ICONE)
        dessin = ImageDraw.Draw(image)
        police, accents = _police(int(taille * (0.34 if masque else 0.42)))
        texte = etab.initiales if accents else _sans_accents(etab.initiales)
        dessin.text((taille / 2, taille / 2), texte, fill='#ffffff', font=police, anchor='mm')

    tampon = io.BytesIO()
    image.convert('RGB').save(tampon, 'PNG', optimize=True)
    return HttpResponse(tampon.getvalue(), content_type='image/png')


@login_not_required
@require_GET
@cache_control(no_cache=True)
def service_worker(request):
    """Servi depuis la racine (/sw.js) pour contrôler tout le site."""
    contexte = {
        'version': version(),
        'page_hors_ligne': reverse('pwa_hors_ligne'),
        'fichiers': json.dumps([
            reverse('pwa_hors_ligne'),
            static('css/app.css'),
            static('js/app.js'),
            static('vendor/bootstrap/bootstrap.min.css'),
            static('vendor/bootstrap/bootstrap.bundle.min.js'),
            static('vendor/bootstrap-icons/bootstrap-icons.min.css'),
        ]),
        'prefixe_static': settings.STATIC_URL,
    }
    reponse = render(request, 'core/sw.js', contexte, content_type='application/javascript')
    reponse['Service-Worker-Allowed'] = '/'
    return reponse


@login_not_required
@require_GET
def hors_ligne(request):
    """Affichée par le service worker quand le réseau ne répond pas."""
    return render(request, 'core/hors_ligne.html', {'etablissement': Etablissement.charger()})
