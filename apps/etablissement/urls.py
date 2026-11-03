from django.urls import path

from . import views

app_name = 'etablissement'

urlpatterns = [
    path('', views.parametres, name='parametres'),
]
