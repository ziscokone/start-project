"""Filtres d'affichage communs. Usage : {% load affichage %}"""
import re

from django import template

register = template.Library()

# L'ordre compte : Edge et Opera contiennent aussi « Chrome », et Chrome contient « Safari ».
NAVIGATEURS = [
    ('Edge', r'Edg(?:e|A|iOS)?/(\d+)'),
    ('Opera', r'OPR/(\d+)'),
    ('Firefox', r'(?:Firefox|FxiOS)/(\d+)'),
    ('Chrome', r'(?:Chrome|CriOS)/(\d+)'),
    ('Safari', r'Version/(\d+).*Safari'),
]
SYSTEMES = [
    ('Android', 'Android'),
    ('iOS', 'iPhone'),
    ('iOS', 'iPad'),
    ('Windows', 'Windows'),
    ('macOS', 'Mac OS X'),
    ('Linux', 'Linux'),
]


@register.filter
def navigateur(user_agent):
    """« Mozilla/5.0 (X11; Linux x86_64) … Chrome/130… » -> « Chrome 130 · Linux »."""
    if not user_agent:
        return '—'
    nom = 'Navigateur inconnu'
    for libelle, motif in NAVIGATEURS:
        trouve = re.search(motif, user_agent)
        if trouve:
            nom = f'{libelle} {trouve.group(1)}'
            break
    systeme = next((libelle for libelle, cle in SYSTEMES if cle in user_agent), None)
    return f'{nom} · {systeme}' if systeme else nom
