from django.db import models

from core.validators import valider_image, valider_telephone


class Etablissement(models.Model):
    """Fiche unique de l'établissement (une seule ligne, pk = 1)."""

    # Identité
    nom = models.CharField("Nom", max_length=200, default="Mon établissement")
    sigle = models.CharField("Sigle", max_length=30, blank=True)
    slogan = models.CharField("Slogan", max_length=200, blank=True)
    logo = models.ImageField("Logo", upload_to='etablissement/', blank=True, null=True,
                             validators=[valider_image])
    description = models.TextField("Activité", blank=True,
                                   help_text="Une ou deux phrases sur l'activité.")

    # Coordonnées
    adresse = models.CharField("Adresse", max_length=255, blank=True)
    ville = models.CharField("Ville", max_length=100, blank=True, default="Abidjan")
    pays = models.CharField("Pays", max_length=100, blank=True, default="Côte d'Ivoire")
    boite_postale = models.CharField("Boîte postale", max_length=100, blank=True)
    telephone = models.CharField("Téléphone principal", max_length=15, blank=True,
                                 validators=[valider_telephone])
    telephone_2 = models.CharField("Téléphone secondaire", max_length=15, blank=True,
                                   validators=[valider_telephone])
    email = models.EmailField("Email", blank=True)
    site_web = models.URLField("Site web", blank=True)

    # Informations légales
    rccm = models.CharField("RCCM", max_length=100, blank=True,
                            help_text="Registre du commerce et du crédit mobilier.")
    compte_contribuable = models.CharField("N° compte contribuable", max_length=100, blank=True)
    regime_fiscal = models.CharField("Régime fiscal", max_length=100, blank=True)
    capital = models.CharField("Capital social", max_length=100, blank=True)

    # Documents imprimés
    devise = models.CharField("Devise", max_length=10, default="FCFA")
    pied_de_page = models.TextField("Pied de page des documents", blank=True,
                                    help_text="Affiché en bas des factures, reçus et rapports.")

    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Établissement"
        verbose_name_plural = "Établissement"

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # La fiche ne se supprime pas.

    @classmethod
    def charger(cls):
        objet, _ = cls.objects.get_or_create(pk=1)
        return objet

    @property
    def nom_court(self):
        return self.sigle or self.nom

    @property
    def initiales(self):
        mots = [m for m in self.nom_court.split() if m]
        return ''.join(m[0] for m in mots[:2]).upper() or 'E'
