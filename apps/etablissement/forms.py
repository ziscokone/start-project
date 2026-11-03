from django import forms

from core.forms import BootstrapMixin, TelephoneField

from .models import Etablissement


class EtablissementForm(BootstrapMixin, forms.ModelForm):
    telephone = TelephoneField(label="Téléphone principal", required=False)
    telephone_2 = TelephoneField(label="Téléphone secondaire", required=False)

    class Meta:
        model = Etablissement
        exclude = ('date_modification',)
        widgets = {
            'logo': forms.FileInput(attrs={'accept': 'image/*'}),
            'description': forms.Textarea(attrs={'rows': 2}),
            'pied_de_page': forms.Textarea(attrs={'rows': 2}),
        }
