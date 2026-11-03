from django.urls import path

from . import views_compte

app_name = 'compte'

urlpatterns = [
    path('connexion/', views_compte.ConnexionView.as_view(), name='connexion'),
    path('deconnexion/', views_compte.DeconnexionView.as_view(), name='deconnexion'),
    path('profil/', views_compte.profil, name='profil'),
    path('mot-de-passe/', views_compte.mot_de_passe, name='mot_de_passe'),
]
