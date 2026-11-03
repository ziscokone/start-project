from django.apps import AppConfig
from django.db.models.signals import post_migrate


def synchroniser_modules(sender, using='default', **kwargs):
    """Crée ou met à jour une ligne Module pour chaque module déclaré dans le code."""
    from core import modules

    from .models import Module

    for definition in modules.tous():
        Module.objects.using(using).update_or_create(
            cle=definition.cle,
            defaults={'nom': definition.nom, 'ordre': definition.ordre},
        )


class ComptesConfig(AppConfig):
    name = 'apps.comptes'
    label = 'comptes'
    verbose_name = 'Comptes et accès'

    def ready(self):
        post_migrate.connect(synchroniser_modules, sender=self)
