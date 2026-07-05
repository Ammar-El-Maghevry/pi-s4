"""
Tests du moteur de calcul de présence (couche pure, sans base de données).

On teste directement les fonctions pures :
- `build_intervals` : reconstruction des intervalles depuis les événements ;
- `compute_session` : statut present/late/absent selon le chevauchement.

Les seuils utilisés dans les tests sont ceux par défaut :
present ≥ 0.70, late ≥ 0.20.
"""
from datetime import date, datetime, time
from types import SimpleNamespace

from app.models.enums import AttendanceStatus, EventType
from app.services.attendance.engine import compute_session, session_window
from app.services.attendance.intervals import Interval, build_intervals

DAY = date(2026, 3, 2)

# Deux séances de référence (90 minutes chacune).
SESSION_A = session_window(DAY, time(8, 0), time(9, 30))    # 08:00 → 09:30
SESSION_B = session_window(DAY, time(9, 45), time(11, 15))  # 09:45 → 11:15


def _event(hour, minute, event_type):
    """Fabrique un faux événement (objet minimal accepté par build_intervals)."""
    return SimpleNamespace(
        timestamp=datetime.combine(DAY, time(hour, minute)),
        event_type=event_type,
    )


def _dt(hour, minute):
    return datetime.combine(DAY, time(hour, minute))


# --------------------------------------------------------------------------- #
# Reconstruction des intervalles                                              #
# --------------------------------------------------------------------------- #

def test_intervalles_paire_simple():
    events = [_event(8, 0, EventType.ENTRY), _event(9, 30, EventType.EXIT)]
    intervals = build_intervals(events)
    assert intervals == [Interval(_dt(8, 0), _dt(9, 30))]


def test_intervalles_entree_en_double_ignoree():
    # Deux entrées de suite : on garde la première, un seul intervalle.
    events = [
        _event(8, 0, EventType.ENTRY),
        _event(8, 10, EventType.ENTRY),
        _event(9, 0, EventType.EXIT),
    ]
    intervals = build_intervals(events)
    assert intervals == [Interval(_dt(8, 0), _dt(9, 0))]


def test_intervalles_sortie_orpheline_ignoree():
    # Une sortie sans entrée ouverte est ignorée.
    events = [_event(8, 0, EventType.EXIT), _event(8, 30, EventType.ENTRY), _event(9, 0, EventType.EXIT)]
    intervals = build_intervals(events)
    assert intervals == [Interval(_dt(8, 30), _dt(9, 0))]


def test_intervalles_sortie_manquante_reste_ouvert():
    events = [_event(8, 0, EventType.ENTRY)]
    intervals = build_intervals(events)
    assert intervals == [Interval(_dt(8, 0), None)]


def test_intervalles_non_ordonnes_sont_tries():
    # Les événements arrivent dans le désordre : le moteur les trie.
    events = [_event(9, 0, EventType.EXIT), _event(8, 0, EventType.ENTRY)]
    intervals = build_intervals(events)
    assert intervals == [Interval(_dt(8, 0), _dt(9, 0))]


# --------------------------------------------------------------------------- #
# Calcul du statut par séance                                                 #
# --------------------------------------------------------------------------- #

def test_present_toute_la_seance():
    intervals = [Interval(_dt(8, 0), _dt(9, 30))]
    res = compute_session(intervals, *SESSION_A)
    assert res.status == AttendanceStatus.PRESENT
    assert res.overlap_ratio == 1.0
    assert res.entry_time == _dt(8, 0)
    assert res.exit_time == _dt(9, 30)


def test_presence_partielle_donne_late():
    # 08:00 → 08:40 = 40 min sur 90 = 0.44 → entre 0.20 et 0.70 → late.
    intervals = [Interval(_dt(8, 0), _dt(8, 40))]
    res = compute_session(intervals, *SESSION_A)
    assert res.status == AttendanceStatus.LATE
    assert round(res.overlap_ratio, 3) == round(40 / 90, 3)


def test_presence_trop_faible_donne_absent():
    # 08:00 → 08:10 = 10 min sur 90 = 0.11 → sous 0.20 → absent.
    intervals = [Interval(_dt(8, 0), _dt(8, 10))]
    res = compute_session(intervals, *SESSION_A)
    assert res.status == AttendanceStatus.ABSENT


def test_aucune_presence_donne_absent():
    res = compute_session([], *SESSION_A)
    assert res.status == AttendanceStatus.ABSENT
    assert res.overlap_ratio == 0.0
    assert res.entry_time is None
    assert res.exit_time is None


def test_presence_hors_seance_ignoree():
    # Présent avant la séance uniquement (07:00 → 07:50) → aucun chevauchement.
    intervals = [Interval(_dt(7, 0), _dt(7, 50))]
    res = compute_session(intervals, *SESSION_A)
    assert res.status == AttendanceStatus.ABSENT
    assert res.overlap_ratio == 0.0


def test_entrees_sorties_multiples_cumulent_le_chevauchement():
    # 08:00→08:30 (30) + 08:45→09:30 (45) = 75 min / 90 = 0.83 → present.
    intervals = [
        Interval(_dt(8, 0), _dt(8, 30)),
        Interval(_dt(8, 45), _dt(9, 30)),
    ]
    res = compute_session(intervals, *SESSION_A)
    assert res.status == AttendanceStatus.PRESENT
    assert round(res.overlap_ratio, 3) == round(75 / 90, 3)
    assert res.entry_time == _dt(8, 0)   # première entrée
    assert res.exit_time == _dt(9, 30)   # dernière sortie


def test_sortie_manquante_compte_jusqu_a_la_fin():
    # Entrée à 08:00 sans sortie → présent jusqu'à la fin de la séance (present),
    # et l'heure de sortie n'est pas renseignée.
    intervals = [Interval(_dt(8, 0), None)]
    res = compute_session(intervals, *SESSION_A)
    assert res.status == AttendanceStatus.PRESENT
    assert res.overlap_ratio == 1.0
    assert res.entry_time == _dt(8, 0)
    assert res.exit_time is None


def test_sortie_manquante_presence_partielle():
    # Entrée tardive à 08:50 sans sortie → 40 min jusqu'à 09:30 → late, sortie None.
    intervals = [Interval(_dt(8, 50), None)]
    res = compute_session(intervals, *SESSION_A)
    assert res.status == AttendanceStatus.LATE
    assert res.exit_time is None


def test_chevauchement_sur_deux_seances_evaluees_independamment():
    # Un seul intervalle 09:00 → 10:30 touche les deux séances.
    intervals = [Interval(_dt(9, 0), _dt(10, 30))]

    # Séance A (08:00→09:30) : chevauchement 09:00→09:30 = 30 min / 90 = 0.33 → late.
    res_a = compute_session(intervals, *SESSION_A)
    assert res_a.status == AttendanceStatus.LATE
    assert round(res_a.overlap_ratio, 3) == round(30 / 90, 3)
    assert res_a.exit_time == _dt(9, 30)  # borné à la fin de la séance A

    # Séance B (09:45→11:15) : chevauchement 09:45→10:30 = 45 min / 90 = 0.5 → late.
    res_b = compute_session(intervals, *SESSION_B)
    assert res_b.status == AttendanceStatus.LATE
    assert round(res_b.overlap_ratio, 3) == round(45 / 90, 3)
    assert res_b.entry_time == _dt(9, 45)  # borné au début de la séance B


def test_seuils_personnalises():
    # Avec un seuil présent très bas, 10 min suffisent.
    intervals = [Interval(_dt(8, 0), _dt(8, 10))]
    res = compute_session(intervals, *SESSION_A, present_threshold=0.1, late_threshold=0.05)
    assert res.status == AttendanceStatus.PRESENT
