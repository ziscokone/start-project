from django.urls import path

from . import views

app_name = 'comptes'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('liste/', views.utilisateur_list, name='utilisateur_list'),
    path('nouveau/', views.utilisateur_create, name='utilisateur_create'),
    path('<int:pk>/modifier/', views.utilisateur_update, name='utilisateur_update'),
    path('<int:pk>/activer/', views.utilisateur_toggle, name='utilisateur_toggle'),
    path('<int:pk>/mot-de-passe/', views.utilisateur_password, name='utilisateur_password'),
    path('<int:pk>/supprimer/', views.utilisateur_delete, name='utilisateur_delete'),
    path('droits/', views.droits, name='droits'),
    path('journal/', views.journal, name='journal'),
    path('bloques/', views.bloques, name='bloques'),
]
