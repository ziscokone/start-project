from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

valider_telephone = RegexValidator(
    r'^\d{8,15}$',
    "Le numéro doit contenir uniquement des chiffres (8 à 15).",
)

TAILLE_IMAGE_MAX_MO = 2


def valider_image(fichier):
    if fichier and fichier.size > TAILLE_IMAGE_MAX_MO * 1024 * 1024:
        raise ValidationError(f"L'image ne doit pas dépasser {TAILLE_IMAGE_MAX_MO} Mo.")
