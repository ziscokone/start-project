from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from core.validators import valider_image, valider_telephone


class Module(models.Model):
    """
    Module de l'application, pour les droits d'accès.

    Les lignes sont créées automatiquement depuis les fichiers module.py à chaque
    `migrate`. Décocher « actif » masque le module pour tout le monde.
    """
    cle = models.SlugField("Clé", max_length=50, unique=True)
    nom = models.CharField("Nom", max_length=100)
    ordre = models.PositiveSmallIntegerField("Ordre", default=100)
    actif = models.BooleanField("Actif", default=True)

    class Meta:
        ordering = ('ordre', 'nom')
        verbose_name = "Module"

    def __str__(self):
        return self.nom


class Role(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super Admin'
    ADMIN = 'admin', 'Administrateur'
    UTILISATEUR = 'utilisateur', 'Utilisateur'


# Plus le rang est haut, plus le rôle a de pouvoir.
RANG = {Role.SUPER_ADMIN: 3, Role.ADMIN: 2, Role.UTILISATEUR: 1}

DESCRIPTION_ROLES = {
    Role.SUPER_ADMIN: "Tous les modules, les paramètres de l'établissement et tous les comptes.",
    Role.ADMIN: "Tous les modules. Gère les administrateurs et les utilisateurs.",
    Role.UTILISATEUR: "Uniquement les modules cochés sur sa fiche.",
}


class UtilisateurManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', Role.SUPER_ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class Utilisateur(AbstractUser):
    Role = Role

    telephone = models.CharField("Téléphone", max_length=15, blank=True, validators=[valider_telephone])
    poste = models.CharField("Fonction", max_length=100, blank=True)
    photo = models.ImageField("Photo", upload_to='utilisateurs/', blank=True, null=True,
                              validators=[valider_image])
    role = models.CharField("Rôle", max_length=20, choices=Role.choices, default=Role.UTILISATEUR)
    modules_autorises = models.ManyToManyField(Module, blank=True, related_name='utilisateurs',
                                               verbose_name="Modules autorisés")
    doit_changer_mot_de_passe = models.BooleanField("Doit changer son mot de passe", default=False)
    cree_par = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='+', verbose_name="Créé par")

    objects = UtilisateurManager()

    class Meta:
        ordering = ('last_name', 'first_name', 'username')
        verbose_name = "Utilisateur"

    def __str__(self):
        return self.nom_affiche

    def save(self, *args, **kwargs):
        # Seul le Super Admin ouvre l'administration Django.
        self.is_superuser = self.is_staff = self.role == Role.SUPER_ADMIN
        super().save(*args, **kwargs)

    # ── Affichage ──
    @property
    def nom_affiche(self):
        return self.get_full_name() or self.username

    @property
    def prenom_court(self):
        return self.first_name.split()[0] if self.first_name.strip() else self.username

    @property
    def initiales(self):
        lettres = (self.first_name[:1] + self.last_name[:1]) or self.username[:2]
        return lettres.upper()

    # ── Droits ──
    @property
    def rang(self):
        return RANG.get(self.role, 0)

    @property
    def est_super_admin(self):
        return self.role == Role.SUPER_ADMIN

    @property
    def est_admin(self):
        """Super Admin ou Administrateur : accès à tous les modules."""
        return self.role in (Role.SUPER_ADMIN, Role.ADMIN)

    def peut_gerer(self, cible):
        """Peut modifier la fiche de `cible` (rang égal ou inférieur)."""
        return self.rang >= cible.rang

    def roles_attribuables(self):
        return [(valeur, libelle) for valeur, libelle in Role.choices if RANG[valeur] <= self.rang]

    def peut_acceder(self, cle_module):
        from core.modules import modules_pour
        return any(m.cle == cle_module for m in modules_pour(self))
