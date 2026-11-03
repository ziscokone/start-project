from django.contrib import admin

from .models import Etablissement


@admin.register(Etablissement)
class EtablissementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville', 'telephone', 'email')

    def has_add_permission(self, request):
        return not Etablissement.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
