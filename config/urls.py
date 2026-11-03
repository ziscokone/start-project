from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.urls import include, path, re_path
from django.views.static import serve

from core import pwa, views as core_views

urlpatterns = [
    path('', core_views.hub, name='hub'),
    path('compte/', include('apps.comptes.urls_compte', namespace='compte')),
    path('utilisateurs/', include('apps.comptes.urls', namespace='comptes')),
    path('parametres/', include('apps.etablissement.urls', namespace='etablissement')),
    path(settings.ADMIN_URL, admin.site.urls),

    # Application installable (PWA)
    path('manifest.webmanifest', pwa.manifeste, name='pwa_manifeste'),
    path('sw.js', pwa.service_worker, name='pwa_sw'),
    path('pwa/icone-<int:taille>.png', pwa.icone, name='pwa_icone'),
    path('hors-ligne/', pwa.hors_ligne, name='pwa_hors_ligne'),
]

if settings.DEBUG:
    # En production, nginx sert /media/ directement.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', login_not_required(serve), {'document_root': settings.MEDIA_ROOT}),
    ]

handler403 = 'core.views.erreur_403'
handler404 = 'core.views.erreur_404'
handler500 = 'core.views.erreur_500'
