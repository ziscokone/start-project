/* Comportements communs à toutes les pages. */
(function () {
    'use strict';

    var html = document.documentElement;

    // ── Menu vertical : réduire / ouvrir ──────────────────────────────────
    document.addEventListener('click', function (e) {
        var cible = e.target.closest('[data-action]');
        if (!cible) return;
        var action = cible.getAttribute('data-action');
        if (action === 'replier-sidebar') {
            var reduite = html.classList.toggle('sidebar-reduite');
            localStorage.setItem('sidebar-reduite', reduite ? '1' : '0');
        } else if (action === 'ouvrir-sidebar') {
            html.classList.add('sidebar-ouverte');
        } else if (action === 'fermer-sidebar') {
            html.classList.remove('sidebar-ouverte');
        }
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') html.classList.remove('sidebar-ouverte');
    });
    // Réactive les animations après le premier affichage (évite le « saut » au chargement).
    requestAnimationFrame(function () { html.classList.remove('sans-transition'); });

    // ── Horloge du hub ────────────────────────────────────────────────────
    var date = document.getElementById('horloge-date');
    var heure = document.getElementById('horloge-heure');
    if (date && heure) {
        var maj = function () {
            var maintenant = new Date();
            date.textContent = maintenant.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
            heure.textContent = maintenant.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        };
        maj();
        setInterval(maj, 1000);
    }

    // ── Téléphones : chiffres uniquement, 15 au maximum ──────────────────
    document.addEventListener('input', function (e) {
        if (e.target.matches('[data-telephone]')) {
            var propre = e.target.value.replace(/\D/g, '').slice(0, 15);
            if (propre !== e.target.value) e.target.value = propre;
        }
    });

    // ── Aperçu d'une image avant envoi ────────────────────────────────────
    document.addEventListener('change', function (e) {
        var champ = e.target;
        if (!champ.matches('[data-apercu]') || !champ.files || !champ.files[0]) return;
        var zone = document.querySelector(champ.getAttribute('data-apercu'));
        if (!zone) return;
        var lecteur = new FileReader();
        lecteur.onload = function (ev) { zone.innerHTML = '<img src="' + ev.target.result + '" alt="">'; };
        lecteur.readAsDataURL(champ.files[0]);
    });

    // ── Filtres automatiques ──────────────────────────────────────────────
    // Un <form data-filtre-auto> se met à jour tout seul : à la saisie (après une
    // courte pause) ou au changement d'une liste. Seules les zones marquées
    // data-filtre-zone="nom" sont remplacées : la page ne se recharge pas et le
    // curseur reste dans le champ de recherche.
    document.querySelectorAll('form[data-filtre-auto]').forEach(function (form) {
        var minuterie = null;
        var derniere = null;

        var appliquer = function () {
            var params = new URLSearchParams(new FormData(form));
            // On retire les champs vides pour garder une adresse propre.
            Array.from(params.keys()).forEach(function (cle) { if (!params.get(cle)) params.delete(cle); });
            var url = (form.getAttribute('action') || window.location.pathname) + (params.toString() ? '?' + params : '');
            if (url === derniere) return;
            derniere = url;
            form.classList.add('filtre-en-cours');
            fetch(url, { headers: { 'X-Requested-With': 'fetch' } })
                .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
                .then(function (texte) {
                    if (url !== derniere) return; // une saisie plus récente est en route
                    var doc = new DOMParser().parseFromString(texte, 'text/html');
                    document.querySelectorAll('[data-filtre-zone]').forEach(function (zone) {
                        var nouvelle = doc.querySelector('[data-filtre-zone="' + zone.getAttribute('data-filtre-zone') + '"]');
                        if (nouvelle) zone.replaceWith(nouvelle);
                    });
                    history.replaceState(null, '', url);
                })
                .catch(function () { form.submit(); })
                .finally(function () { form.classList.remove('filtre-en-cours'); });
        };

        form.addEventListener('input', function (e) {
            if (e.target.tagName === 'SELECT') return;
            clearTimeout(minuterie);
            minuterie = setTimeout(appliquer, 350);
        });
        form.addEventListener('change', function (e) {
            if (e.target.tagName === 'SELECT') { clearTimeout(minuterie); appliquer(); }
        });
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            clearTimeout(minuterie);
            appliquer();
        });
    });

    // ── Application installable (PWA) ─────────────────────────────────────
    // Le service worker permet l'installation et affiche une page hors ligne.
    if ('serviceWorker' in navigator && html.dataset.sw) {
        window.addEventListener('load', function () {
            navigator.serviceWorker.register(html.dataset.sw, { scope: '/' }).catch(function () {});
        });
    }

    // Le bouton « Installer l'application » n'apparaît que si l'installation est possible.
    var invitation = null;
    var estIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) ||
                 (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    var dejaInstallee = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
    var afficherBoutons = function (visible) {
        document.querySelectorAll('[data-pwa-installer]').forEach(function (el) { el.hidden = !visible; });
    };

    // Chrome, Edge, Android : le navigateur propose l'installation.
    window.addEventListener('beforeinstallprompt', function (e) {
        e.preventDefault();          // on garde l'invitation pour notre propre bouton
        invitation = e;
        afficherBoutons(true);
    });
    window.addEventListener('appinstalled', function () {
        invitation = null;
        afficherBoutons(false);
    });
    // iPhone / iPad : pas d'invitation automatique, on affiche une aide.
    if (estIOS && !dejaInstallee) afficherBoutons(true);

    document.addEventListener('click', function (e) {
        if (!e.target.closest('[data-action="installer-app"]')) return;
        e.preventDefault();
        if (invitation) {
            invitation.prompt();
            invitation.userChoice.finally(function () { invitation = null; afficherBoutons(false); });
        } else if (estIOS) {
            bootstrap.Modal.getOrCreateInstance(document.getElementById('aide-installation')).show();
        }
    });

    // ── Confirmation avant une action ─────────────────────────────────────
    document.addEventListener('submit', function (e) {
        var message = e.target.getAttribute('data-confirmer');
        if (message && !window.confirm(message)) e.preventDefault();
    });

    // ── Fiche utilisateur : modules visibles seulement pour le rôle Utilisateur
    var role = document.getElementById('id_role');
    var blocModules = document.getElementById('bloc-modules');
    if (role && blocModules) {
        var basculer = function () {
            var simple = role.value === 'utilisateur';
            blocModules.querySelector('[data-si-utilisateur]').hidden = !simple;
            blocModules.querySelector('[data-si-admin]').hidden = simple;
        };
        role.addEventListener('change', basculer);
        basculer();
    }

    // ── Les messages de succès disparaissent seuls ────────────────────────
    setTimeout(function () {
        document.querySelectorAll('.alert-success.alert-dismissible').forEach(function (el) {
            if (window.bootstrap) bootstrap.Alert.getOrCreateInstance(el).close();
        });
    }, 5000);
})();
