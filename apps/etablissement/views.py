from django.contrib import messages
from django.shortcuts import redirect, render

from core.permissions import super_admin_requis

from .forms import EtablissementForm
from .models import Etablissement


@super_admin_requis
def parametres(request):
    etablissement = Etablissement.charger()
    if request.method == 'POST':
        form = EtablissementForm(request.POST, request.FILES, instance=etablissement)
        if form.is_valid():
            if request.POST.get('retirer_logo') and not request.FILES.get('logo'):
                form.instance.logo.delete(save=False)
                form.instance.logo = None
            form.save()
            messages.success(request, "Paramètres de l'établissement enregistrés.")
            return redirect('etablissement:parametres')
        messages.error(request, "Vérifiez les champs signalés.")
    else:
        form = EtablissementForm(instance=etablissement)
    return render(request, 'etablissement/parametres.html', {'form': form})
