"""
Tests des helpers de parsing de l'import de l'emploi du temps (couche pure,
sans base de données).

Couvre : reconnaissance des alias d'en-tetes (via le lecteur de feuilles de
calcul partage), parsing des heures, et resolution des fenetres de pointage
par defaut.
"""
from app.services.schedules_import import (
    DEFAULT_CHECK_IN_OFFSET,
    DEFAULT_CHECK_OUT_OFFSET,
    _HEADER_ALIASES,
    _parse_offset,
    _parse_time,
)
from app.services.spreadsheet import read_csv_rows


# ------------------------------- En-tetes ------------------------------- #

def test_rows_from_csv_en_tetes_alias():
    content = (
        "Séance,Enseignant,Salle,Jour,Heure_debut,Heure_fin,Classe\n"
        "Maths,Mme Curie,A101,Monday,08:00,09:30,CS 1\n"
    ).encode()
    rows = read_csv_rows(content, _HEADER_ALIASES)
    assert rows == [
        {
            "name": "Maths",
            "teacher": "Mme Curie",
            "room": "A101",
            "day": "Monday",
            "start_time": "08:00",
            "end_time": "09:30",
            "class_name": "CS 1",
        }
    ]


def test_rows_from_csv_offsets_optionnels():
    content = (
        "name,teacher,room,day,start_time,end_time,check_in,check_out\n"
        "Physics,Dr Newton,B203,Tuesday,10:00,11:30,10,5\n"
    ).encode()
    rows = read_csv_rows(content, _HEADER_ALIASES)
    assert rows[0]["check_in_offset_minutes"] == "10"
    assert rows[0]["check_out_offset_minutes"] == "5"


# ------------------------------- Heures ------------------------------- #

def test_parse_time_hh_mm():
    t = _parse_time("08:05")
    assert t is not None and t.hour == 8 and t.minute == 5


def test_parse_time_hh_mm_ss():
    t = _parse_time("08:05:00")
    assert t is not None and t.hour == 8 and t.minute == 5


def test_parse_time_invalide():
    assert _parse_time("not-a-time") is None
    assert _parse_time("25:99") is None


# ------------------------------- Fenetres de pointage ------------------------------- #

def test_parse_offset_valeur_par_defaut_si_absente():
    assert _parse_offset("", 15) == 15


def test_parse_offset_valeur_fournie():
    assert _parse_offset("20", DEFAULT_CHECK_IN_OFFSET) == 20
    assert _parse_offset("5.0", DEFAULT_CHECK_OUT_OFFSET) == 5


def test_parse_offset_invalide():
    assert _parse_offset("beaucoup", 15) is None
