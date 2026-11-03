import re

from django import forms

from core.validators import valider_telephone


class TelephoneField(forms.CharField):
    """Téléphone : chiffres uniquement, 8 à 15. Espaces, points et tirets sont retirés."""

    default_validators = [valider_telephone]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 15)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        return re.sub(r'[\s.\-]', '', value) if value else value

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs.update({'inputmode': 'numeric', 'data-telephone': '1', 'placeholder': '0700000000'})
        return attrs


class BootstrapMixin:
    """Ajoute les classes Bootstrap aux champs d'un formulaire."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nom, champ in self.fields.items():
            widget = champ.widget
            if isinstance(widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                continue
            if isinstance(widget, forms.CheckboxInput):
                classe = 'form-check-input'
            elif isinstance(widget, forms.Select):
                classe = 'form-select'
            else:
                classe = 'form-control'
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {classe}".strip()

    def full_clean(self):
        # Après validation : bordure rouge sur les champs en erreur.
        super().full_clean()
        for nom in self.errors:
            if nom in self.fields:
                attrs = self.fields[nom].widget.attrs
                if 'is-invalid' not in attrs.get('class', ''):
                    attrs['class'] = f"{attrs.get('class', '')} is-invalid".strip()
