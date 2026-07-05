"""
Reconstruction des intervalles de présence à partir des événements bruts.

Le moteur ne raisonne pas directement sur les événements (entrée / sortie) mais
sur des **intervalles** « présent de t1 à t2 ». Cette reconstruction est une
fonction pure (aucune dépendance à la base de données), ce qui la rend simple à
tester.

Règles de reconstruction :

- Une ENTRÉE ouvre un intervalle ; une SORTIE le ferme.
- Entrées multiples consécutives (sans sortie intermédiaire) : on conserve la
  PREMIÈRE entrée (les doublons d'entrée sont ignorés).
- Sortie orpheline (sans entrée ouverte) : ignorée.
- Entrée jamais suivie d'une sortie (sortie manquante) : l'intervalle reste
  « ouvert » (fin = None). Le calcul de chevauchement le traitera comme une
  présence courant jusqu'à la fin de la séance.
"""
from dataclasses import dataclass
from datetime import datetime

from app.models.enums import EventType


@dataclass
class Interval:
    """Un intervalle de présence. `end is None` = sortie manquante (encore présent)."""
    start: datetime
    end: datetime | None


def _naive(dt: datetime) -> datetime:
    """
    Ramène un datetime « aware » (avec fuseau) en datetime « naïf » LOCAL.

    Les événements en base sont horodatés avec fuseau, tandis que les horodatages
    injectés en test peuvent être naïfs. Mélanger les deux provoque une erreur
    lors des soustractions. On convertit d'abord vers l'heure locale du serveur
    (celle des fenêtres de séance) AVANT de retirer le fuseau : supprimer le
    fuseau sans convertir décalerait tout événement reçu avec un offset non
    local (ex. un timestamp en +00:00 sur un serveur en UTC+2).
    """
    return dt.astimezone().replace(tzinfo=None) if dt.tzinfo is not None else dt


def build_intervals(events) -> list[Interval]:
    """
    Reconstruit les intervalles de présence à partir d'une liste d'événements.

    `events` : itérable d'objets possédant `.event_type` (EventType) et
    `.timestamp` (datetime). L'ordre d'entrée n'importe pas : on trie par
    horodatage.
    """
    ordered = sorted(events, key=lambda e: _naive(e.timestamp))

    intervals: list[Interval] = []
    open_start: datetime | None = None

    for event in ordered:
        ts = _naive(event.timestamp)
        if event.event_type == EventType.ENTRY:
            if open_start is None:
                open_start = ts
            # Sinon : entrée en double, on garde la première ouverture.
        else:  # EventType.EXIT
            if open_start is not None:
                intervals.append(Interval(start=open_start, end=ts))
                open_start = None
            # Sinon : sortie orpheline, ignorée.

    # Intervalle resté ouvert = sortie manquante.
    if open_start is not None:
        intervals.append(Interval(start=open_start, end=None))

    return intervals
