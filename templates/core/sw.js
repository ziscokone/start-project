{% autoescape off %}/* Service worker : généré par core/pwa.py (ne pas servir en fichier statique).
 *
 * - Pages : toujours depuis le réseau (données à jour, sessions respectées).
 *   Si le réseau ne répond pas, on affiche la page hors ligne.
 * - Fichiers statiques (CSS, JS, polices, icônes) : depuis le cache, mis à jour
 *   en arrière-plan. L'application démarre ainsi beaucoup plus vite.
 */
const CACHE = 'app-{{ version }}';
const PAGE_HORS_LIGNE = '{{ page_hors_ligne }}';
const FICHIERS = {{ fichiers }};
const PREFIXE_STATIC = '{{ prefixe_static }}';

self.addEventListener('install', (e) => {
    e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FICHIERS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
    // Supprime les caches des versions précédentes.
    e.waitUntil(
        caches.keys()
            .then((noms) => Promise.all(noms.filter((n) => n !== CACHE).map((n) => caches.delete(n))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (e) => {
    const req = e.request;
    if (req.method !== 'GET') return;
    const url = new URL(req.url);
    if (url.origin !== self.location.origin) return;

    // Pages HTML : réseau d'abord, page hors ligne en secours.
    if (req.mode === 'navigate') {
        e.respondWith(fetch(req).catch(() => caches.match(PAGE_HORS_LIGNE)));
        return;
    }

    // Fichiers statiques : cache d'abord, rafraîchi en arrière-plan.
    if (url.pathname.startsWith(PREFIXE_STATIC)) {
        e.respondWith(
            caches.open(CACHE).then((cache) =>
                cache.match(req).then((enCache) => {
                    const reseau = fetch(req).then((rep) => {
                        if (rep.ok) cache.put(req, rep.clone());
                        return rep;
                    }).catch(() => enCache);
                    return enCache || reseau;
                })
            )
        );
    }
});
{% endautoescape %}
