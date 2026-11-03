from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm

from core.forms import BootstrapMixin, TelephoneField
from core.modules import modules_pour

from .models import Module, Role, Utilisateur


class ConnexionForm(AuthenticationForm):
    se_souvenir = forms.BooleanField(label="Se souvenir de moi", required=False, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Identifiant"
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Votre identifiant', 'autofocus': True})
        self.fields['password'].widget.attrs.update({
            'class': 'form-control', 'placeholder': '••••••••'})
        self.fields['se_souvenir'].widget.attrs['class'] = 'form-check-input'

    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': "Identifiant ou mot de passe incorrect.",
        'inactive': "Ce compte est désactivé. Contactez votre administrateur.",
    }


def modules_attribuables(acteur):
    """Un utilisateur ne peut donner que les modules auxquels il a lui-même accès."""
    cles = [m.cle for m in modules_pour(acteur)]
    return Module.objects.filter(actif=True, cle__in=cles)


class UtilisateurForm(BootstrapMixin, forms.ModelForm):
    telephone = TelephoneField(label="Téléphone", required=False)
    modules = forms.ModelMultipleChoiceField(
        label="Modules autorisés", queryset=Module.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Utilisateur
        fields = ('first_name', 'last_name', 'username', 'email', 'telephone', 'poste',
                  'photo', 'role', 'is_active')
        labels = {'first_name': "Prénoms", 'last_name': "Nom", 'username': "Identifiant de connexion",
                  'is_active': "Compte actif"}
        help_texts = {'username': "Lettres, chiffres et @ . + - _ uniquement.", 'is_active': ''}
        widgets = {'photo': forms.FileInput(attrs={'accept': 'image/*'})}

    def __init__(self, *args, acteur, **kwargs):
        super().__init__(*args, **kwargs)
        self.acteur = acteur
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['role'].choices = acteur.roles_attribuables()
        self.fields['modules'].queryset = modules_attribuables(acteur)
        if self.instance.pk:
            self.fields['modules'].initial = self.instance.modules_autorises.all()
        # On ne change pas son propre rôle, son statut ou ses modules.
        if self.instance.pk and self.instance.pk == acteur.pk:
            for nom in ('role', 'is_active', 'modules'):
                self.fields[nom].disabled = True
                self.fields[nom].help_text = "Vous ne pouvez pas modifier ce champ sur votre propre compte."

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and Utilisateur.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cet email est déjà utilisé par un autre compte.")
        return email

    def clean(self):
        donnees = super().clean()
        instance = self.instance
        if instance.pk and instance.est_super_admin and instance.pk != self.acteur.pk:
            retrograde = donnees.get('role') and donnees['role'] != Role.SUPER_ADMIN
            desactive = 'is_active' in donnees and not donnees['is_active']
            if (retrograde or desactive) and dernier_super_admin(instance):
                raise forms.ValidationError("Il doit toujours rester au moins un Super Admin actif.")
        return donnees

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.pk:
            user.cree_par = self.acteur
        user.save()
        if not self.fields['modules'].disabled:
            choisis = set(self.cleaned_data['modules'])
            # Les modules hors de portée de l'acteur sont conservés tels quels.
            hors_portee = set(user.modules_autorises.exclude(pk__in=self.fields['modules'].queryset))
            user.modules_autorises.set(choisis | hors_portee)
        return user


class CreationUtilisateurForm(UtilisateurForm):
    password1 = forms.CharField(label="Mot de passe", strip=False, widget=forms.PasswordInput(
        attrs={'autocomplete': 'new-password'}))
    password2 = forms.CharField(label="Confirmation", strip=False, widget=forms.PasswordInput(
        attrs={'autocomplete': 'new-password'}))
    doit_changer = forms.BooleanField(
        label="Changer le mot de passe à la première connexion", required=False, initial=True)

    def clean_password2(self):
        p1, p2 = self.cleaned_data.get('password1'), self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        return p2

    def _post_clean(self):
        super()._post_clean()
        mot_de_passe = self.cleaned_data.get('password2')
        if mot_de_passe:
            try:
                password_validation.validate_password(mot_de_passe, self.instance)
            except forms.ValidationError as erreur:
                self.add_error('password2', erreur)

    def save(self, commit=True):
        self.instance.set_password(self.cleaned_data['password1'])
        self.instance.doit_changer_mot_de_passe = self.cleaned_data['doit_changer']
        return super().save(commit)


class ReinitialisationForm(BootstrapMixin, SetPasswordForm):
    doit_changer = forms.BooleanField(
        label="Changer le mot de passe à la prochaine connexion", required=False, initial=True)

    def save(self, commit=True):
        self.user.doit_changer_mot_de_passe = self.cleaned_data['doit_changer']
        return super().save(commit)


class ProfilForm(BootstrapMixin, forms.ModelForm):
    telephone = TelephoneField(label="Téléphone", required=False)

    class Meta:
        model = Utilisateur
        fields = ('first_name', 'last_name', 'email', 'telephone', 'photo')
        labels = {'first_name': "Prénoms", 'last_name': "Nom"}
        widgets = {'photo': forms.FileInput(attrs={'accept': 'image/*'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and Utilisateur.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cet email est déjà utilisé par un autre compte.")
        return email


class ChangerMotDePasseForm(BootstrapMixin, PasswordChangeForm):
    pass


def dernier_super_admin(user):
    """Vrai si `user` est le seul Super Admin actif."""
    return not Utilisateur.objects.filter(role=Role.SUPER_ADMIN, is_active=True).exclude(pk=user.pk).exists()
