"""Connexion, déconnexion et espace personnel (accessibles à tout utilisateur connecté)."""
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from .forms import ChangerMotDePasseForm, ConnexionForm, ProfilForm


class ConnexionView(LoginView):
    template_name = 'comptes/connexion.html'
    form_class = ConnexionForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        if not form.cleaned_data.get('se_souvenir'):
            self.request.session.set_expiry(0)  # fermée avec le navigateur
        return super().form_valid(form)


class DeconnexionView(LogoutView):
    next_page = 'compte:connexion'


def profil(request):
    form = ProfilForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST':
        if form.is_valid():
            if request.POST.get('retirer_photo') and not request.FILES.get('photo'):
                form.instance.photo.delete(save=False)
                form.instance.photo = None
            form.save()
            messages.success(request, "Profil enregistré.")
            return redirect('compte:profil')
        messages.error(request, "Vérifiez les champs signalés.")
    return render(request, 'comptes/profil.html', {'form': form})


def mot_de_passe(request):
    form = ChangerMotDePasseForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.doit_changer_mot_de_passe = False
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Mot de passe modifié.")
        return redirect('hub')
    return render(request, 'comptes/mot_de_passe.html', {'form': form})
