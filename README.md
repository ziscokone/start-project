# template-clean

Modèle de départ Django pour les nouveaux projets.

Il contient :

- **la connexion et la déconnexion**, avec blocage après 5 échecs (django-axes) ;
- **un hub** : une tuile par module autorisé ;
- **un gabarit de module avec menu vertical** (repliable, sections, badges) et une barre du haut (recherche, modules, notifications, compte) ;
- **le module « Gestion utilisateurs »** : comptes, rôles, droits par module, journal de connexion, comptes bloqués ;
- **les paramètres de l'établissement** : nom, logo, coordonnées, mentions légales, pied de page des documents ;
- **un espace personnel** : profil et changement de mot de passe.

Couleurs : marine `#1e3260` et orange `#E67E22` (reprises de billeterie-etv), dans [static/css/app.css](static/css/app.css).

---

## Démarrer un nouveau projet

```bash
# 1. Copier le modèle
cp -r template-clean mon-projet
cd mon-projet
rm -rf .git db.sqlite3 media my_env     # repartir de zéro
git init

# 2. Environnement Python
python3 -m venv my_env
source my_env/bin/activate
pip install -r requirements.txt

# 3. Configuration
cp .env.example .env                     # puis adapter les valeurs

# 4. Base de données + premier Super Admin
python manage.py init_projet --nom "Mon entreprise"

# 5. Lancer
python manage.py runserver
```

Ensuite, connectez-vous et complétez **Paramètres de l'établissement** (menu de l'avatar).

---

## Les rôles

| Rôle | Accès |
|---|---|
| **Super Admin** | Tous les modules, paramètres de l'établissement, tous les comptes, administration Django. |
| **Administrateur** | Tous les modules. Gère les administrateurs et les utilisateurs. |
| **Utilisateur** | Uniquement les modules cochés sur sa fiche. |

Règles intégrées :

- on ne modifie que les comptes de rang égal ou inférieur au sien ;
- on ne peut ni désactiver, ni supprimer, ni changer le rôle de son propre compte ;
- il reste toujours au moins un Super Admin actif ;
- on ne peut donner que les modules auxquels on a soi-même accès ;
- un mot de passe réinitialisé par un administrateur doit être changé à la connexion suivante.

---

## Ajouter un module

Exemple : un module « Stock ».

**1. Créer l'application**

```bash
mkdir apps/stock
python manage.py startapp stock apps/stock
```

Dans `apps/stock/apps.py`, mettre `name = 'apps.stock'`, puis ajouter `'apps.stock'` à `INSTALLED_APPS` dans [config/settings.py](config/settings.py).

**2. Déclarer les URLs avec un namespace**

```python
# apps/stock/urls.py
app_name = 'stock'
urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('articles/', views.article_list, name='article_list'),
]
```

```python
# config/urls.py
path('stock/', include('apps.stock.urls', namespace='stock')),
```

**3. Déclarer le module dans `apps/stock/module.py`**

```python
from core.modules import DefinitionModule, Lien, Section, enregistrer

enregistrer(DefinitionModule(
    cle='stock',
    nom='Stock',
    description='Articles, entrées et sorties',
    icone='bi-box-seam',            # https://icons.getbootstrap.com
    couleur='orange',               # marine, bleu, vert, violet, orange, rouge, turquoise
    ordre=10,                       # position sur le hub
    url_name='stock:accueil',
    namespaces=('stock',),
    recherche_url='stock:article_list',   # facultatif : la recherche du haut envoie ?q=
    menu=(
        Section('Pilotage', (
            Lien('Tableau de bord', 'stock:accueil', 'bi-speedometer2'),
        )),
        Section('Articles', (
            Lien('Tous les articles', 'stock:article_list', 'bi-box',
                 actif_sur=('stock:article_update',),          # pages qui allument ce lien
                 badge=lambda request: 12),                    # compteur à droite
            Lien('Inventaire', None, 'bi-clipboard-check'),    # url None : « bientôt »
        )),
    ),
))
```

**4. Écrire les pages avec le gabarit module**

```django
{% extends "layouts/module.html" %}
{% block title %}Articles{% endblock %}
{% block page_titre %}Tous les articles{% endblock %}
{% block page_icone %}bi-box{% endblock %}
{% block content %}
<section class="carte">
    <div class="carte-entete"><h3 class="carte-titre">Articles</h3></div>
    <div class="carte-corps">…</div>
</section>
{% endblock %}
```

**5. Lancer `python manage.py migrate`**

C'est tout. Automatiquement :

- la tuile apparaît sur le hub ;
- le module apparaît dans **Droits d'accès** et dans la fiche utilisateur ;
- toute page du namespace `stock` est refusée (erreur 403) à qui n'a pas le droit ;
- le menu vertical s'affiche avec le lien actif.

Pour réserver une page à un rôle : `from core.permissions import admin_requis` puis `@admin_requis` (ou `@super_admin_requis`, `@role_requis('...')`).

Pour afficher des notifications sous la cloche, passez `notifications=ma_fonction` à `DefinitionModule` ; la fonction reçoit `request` et renvoie une liste de `{'icone', 'texte', 'url', 'niveau'}` (`niveau` : `danger`, `alerte`, `orange` ou `marine`).

---

## Repères

| Élément | Emplacement |
|---|---|
| Registre des modules | [core/modules.py](core/modules.py) |
| Contrôle d'accès aux modules | [core/middleware.py](core/middleware.py) |
| Variables globales des gabarits | [core/context_processors.py](core/context_processors.py) |
| Champ téléphone (chiffres, 8 à 15) | [core/forms.py](core/forms.py), [core/validators.py](core/validators.py) |
| Gabarit hub / pages simples | [templates/layouts/page.html](templates/layouts/page.html) |
| Gabarit module (menu vertical) | [templates/layouts/module.html](templates/layouts/module.html) |
| Styles et couleurs | [static/css/app.css](static/css/app.css) |
| Comportements (menu, horloge, aperçus) | [static/js/app.js](static/js/app.js) |
| Initialisation | `python manage.py init_projet` |

Composants CSS prêts à l'emploi : `carte`, `carte-entete`, `carte-corps`, `carte-pied`, `tableau`, `pastille` (`-marine`, `-orange`, `-succes`, `-danger`, `-alerte`), `icone-boite`, `btn-primary`, `btn-accent`, `btn-light-border`, `barre-filtres`, `onglets`, `vide`, `accueil-hero`, `ligne-action`, `liste-personnes`.

---

## Production

Dans `.env` : `DEBUG=False`, une vraie `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, les variables `DB_*` pour PostgreSQL et un `ADMIN_URL` non devinable. Décommenter `psycopg2-binary` et `gunicorn` dans `requirements.txt`, puis :

```bash
python manage.py collectstatic
python manage.py init_projet
```

nginx doit servir `/static/` (dossier `staticfiles/`) et `/media/`.

---

## Application installable (PWA)

Chaque projet peut s'installer comme une application sur téléphone, tablette et ordinateur, sans passer par un store.

- **Rien à configurer** : le nom, le sigle et le logo viennent de **Paramètres de l'établissement**. Les icônes sont générées à partir du logo, ou des initiales sur fond orange s'il n'y a pas de logo.
- **Bouton « Installer l'application »** dans le menu de l'avatar. Il n'apparaît que si l'appareil peut installer l'application. Sur iPhone et iPad, il ouvre une aide (*Partager → Sur l'écran d'accueil*).
- **Hors ligne** : les pages viennent toujours du serveur. Sans réseau, une page « Vous êtes hors ligne » s'affiche.
- **Code** : [core/pwa.py](core/pwa.py), [templates/core/sw.js](templates/core/sw.js), [templates/core/hors_ligne.html](templates/core/hors_ligne.html).

| Adresse | Rôle |
|---|---|
| `/manifest.webmanifest` | Description de l'application (nom, icônes, couleurs) |
| `/sw.js` | Service worker (cache des fichiers statiques, page hors ligne) |
| `/pwa/icone-<180\|192\|512>.png` | Icônes générées |
| `/hors-ligne/` | Page affichée sans réseau |

À savoir :

- **HTTPS obligatoire** en production (`localhost` suffit pour tester).
- `/sw.js` et `/manifest.webmanifest` doivent être transmis à Django par nginx (ne pas les servir comme fichiers statiques).
- Après une mise à jour du CSS ou du JS, augmentez `PWA_VERSION` dans [config/settings.py](config/settings.py) pour vider le cache des appareils.
