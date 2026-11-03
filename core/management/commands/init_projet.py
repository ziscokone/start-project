"""
Prépare une base neuve : établissement, modules et premier Super Admin.

    python manage.py init_projet
    python manage.py init_projet --nom "Garage Kone" --username admin --password "MotDePasse!2026"
"""
import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.comptes.models import Role
from apps.etablissement.models import Etablissement


class Command(BaseCommand):
    help = "Initialise le projet : migrations, établissement, modules et Super Admin."

    def add_arguments(self, parser):
        parser.add_argument('--nom', help="Nom de l'établissement")
        parser.add_argument('--username', help="Identifiant du Super Admin")
        parser.add_argument('--password', help="Mot de passe du Super Admin")
        parser.add_argument('--prenom', default='', help="Prénoms du Super Admin")
        parser.add_argument('--nom-famille', default='', help="Nom du Super Admin")

    def handle(self, *args, **options):
        call_command('migrate', interactive=False, verbosity=0)
        self.stdout.write("✓ Base de données à jour, modules synchronisés")

        etablissement = Etablissement.charger()
        if options['nom']:
            etablissement.nom = options['nom']
            etablissement.save()
        self.stdout.write(f"✓ Établissement : {etablissement.nom}")

        User = get_user_model()
        if User.objects.filter(role=Role.SUPER_ADMIN, is_active=True).exists():
            self.stdout.write("✓ Un Super Admin existe déjà")
            return

        username = options['username'] or input("Identifiant du Super Admin : ").strip()
        if not username:
            raise CommandError("Identifiant obligatoire.")
        if User.objects.filter(username=username).exists():
            raise CommandError(f"L'identifiant « {username} » existe déjà.")

        password = options['password']
        while not password:
            saisie = getpass.getpass("Mot de passe : ")
            if saisie != getpass.getpass("Confirmation : "):
                self.stderr.write("Les mots de passe ne correspondent pas.")
                continue
            try:
                validate_password(saisie)
            except ValidationError as erreur:
                self.stderr.write(" ".join(erreur.messages))
                continue
            password = saisie

        User.objects.create_superuser(
            username=username, password=password,
            first_name=options['prenom'], last_name=options['nom_famille'])
        self.stdout.write(self.style.SUCCESS(f"✓ Super Admin « {username} » créé"))
