"""
Moteur de calcul de présence — cœur du projet.

À partir des intervalles de présence d'un étudiant (voir `intervals.py`) et de
l'emploi du temps, ce module décide, pour chaque séance, un statut :
`present` / `late` / `absent`, en fonction du **taux de chevauchement** entre la
présence de l'étudiant et le créneau de la séance.

Le calcul par séance (`compute_session`) est une fonction pure : il ne dépend
ni de la base de données ni de FastAPI, ce qui le rend directement testable.
L'orchestration qui lit les événements et écrit les résultats se trouve dans
`service.py`.
"""
from dataclasses import dataclass
from datetime import date, datetime

from app.config import settings
from app.models.enums import AttendanceStatus
from app.services.attendance.intervals import Interval, _naive


@dataclass
class SessionComputation:
    """Résultat du calcul pour une séance donnée."""
    status: AttendanceStatus
    overlap_ratio: float           # part du créneau réellement passée en salle (0..1)
    overlap_seconds: float
    entry_time: datetime | None    # première entrée retenue pour la séance
    exit_time: datetime | None     # dernière sortie retenue (None si sortie manquante)


def session_window(on_date: date, start_time, end_time) -> tuple[datetime, datetime]:
    """
    Construit la fenêtre horaire absolue d'une séance pour une date donnée.

    Combine la date du jour avec les heures de début / fin du créneau.
    """
    return datetime.combine(on_date, start_time), datetime.combine(on_date, end_time)


def _overlap_seconds(interval: Interval, window_start: datetime, window_end: datetime) -> float:
    """
    Secondes de chevauchement entre un intervalle de présence et une fenêtre.

    Un intervalle ouvert (sortie manquante) est prolongé jusqu'à la fin de la
    fenêtre : l'étudiant est considéré présent jusqu'à la fin de la séance.
    """
    start = _naive(interval.start)
    end = _naive(interval.end) if interval.end is not None else window_end

    latest_start = max(start, window_start)
    earliest_end = min(end, window_end)
    delta = (earliest_end - latest_start).total_seconds()
    return max(0.0, delta)


def compute_session(
    intervals: list[Interval],
    window_start: datetime,
    window_end: datetime,
    present_threshold: float | None = None,
    late_threshold: float | None = None,
) -> SessionComputation:
    """
    Calcule le statut de présence d'un étudiant pour une séance.

    - Additionne le chevauchement de tous ses intervalles avec le créneau.
    - `overlap_ratio` = temps chevauché / durée de la séance.
    - Statut : `present` si ratio ≥ seuil présent, `late` si ratio ≥ seuil
      retard, `absent` sinon.

    Les intervalles peuvent chevaucher plusieurs séances : chaque séance est
    évaluée indépendamment avec sa propre fenêtre.
    """
    present_threshold = (
        settings.ATTENDANCE_PRESENT_THRESHOLD if present_threshold is None else present_threshold
    )
    late_threshold = (
        settings.ATTENDANCE_LATE_THRESHOLD if late_threshold is None else late_threshold
    )

    total_seconds = (window_end - window_start).total_seconds()
    if total_seconds <= 0:
        # Créneau de durée nulle ou incohérent : rien à calculer.
        return SessionComputation(AttendanceStatus.ABSENT, 0.0, 0.0, None, None)

    overlapped = 0.0
    entry_time: datetime | None = None
    exit_time: datetime | None = None
    has_open = False  # un intervalle chevauchant la séance sans sortie ?

    for interval in intervals:
        seconds = _overlap_seconds(interval, window_start, window_end)
        if seconds <= 0:
            continue  # cet intervalle ne touche pas la séance
        overlapped += seconds

        # Première entrée effective (bornée au début de la séance).
        candidate_entry = max(_naive(interval.start), window_start)
        if entry_time is None or candidate_entry < entry_time:
            entry_time = candidate_entry

        # Dernière sortie effective (bornée à la fin de la séance).
        if interval.end is None:
            has_open = True
        else:
            candidate_exit = min(_naive(interval.end), window_end)
            if exit_time is None or candidate_exit > exit_time:
                exit_time = candidate_exit

    # Une sortie manquante sur la séance prime : on ne retient pas d'heure de sortie.
    if has_open:
        exit_time = None

    ratio = overlapped / total_seconds

    if ratio >= present_threshold:
        status = AttendanceStatus.PRESENT
    elif ratio >= late_threshold:
        status = AttendanceStatus.LATE
    else:
        status = AttendanceStatus.ABSENT

    return SessionComputation(
        status=status,
        overlap_ratio=ratio,
        overlap_seconds=overlapped,
        entry_time=entry_time,
        exit_time=exit_time,
    )
