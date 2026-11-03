from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Module, Utilisateur


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'cle', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'is_active', 'last_login')
    list_filter = ('role', 'is_active')
    filter_horizontal = ('modules_autorises',)
    fieldsets = UserAdmin.fieldsets[:2] + (
        ('Application', {'fields': ('telephone', 'poste', 'photo', 'role', 'modules_autorises',
                                    'doit_changer_mot_de_passe')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
