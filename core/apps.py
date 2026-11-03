from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = 'Cœur'

    def ready(self):
        # Charge le fichier module.py de chaque application installée.
        autodiscover_modules('module')
