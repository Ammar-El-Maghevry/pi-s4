"""
Tests du parseur de grille PDF (couche pure `sessions_from_matrix`, sans
ouverture de fichier PDF).

La matrice utilisee ici est celle reellement extraite par pdfplumber depuis
un export SupNum ("test1.pdf" fourni par l'utilisateur) : elle inclut donc
les lignes parasites reelles (metadonnees, "10 qq", "#REF!") qu'il faut
ignorer, et pas seulement un cas simplifie.
"""
import pytest

from app.services.schedule_grid_pdf import GridPdfParseError, sessions_from_matrix

# Matrice extraite par pdfplumber depuis le PDF reel fourni (semaine du
# 04/05/2026, filiere CNM) : une seule seance renseignee, le mardi, sur 4 des
# 5 creneaux de la journee.
REAL_MATRIX = [
    ["SupNum : Emploi du temps Fillière: CNM"] + [None] * 21,
    ["Semestre : S4 Dépt\n1"] + [None] * 5 + ["CNM", "1 Semaine :", None, None, None, "11", "6 du", None,
     "04/05/2026", None, "au", "09/05/2026", None, "", None, None],
    [None] * 6 + ["2 3 4 5"] + [None] * 15,
    ["", "08h00 à 9H30", None, None, "", "09h45 à 11H15", None, None, "", "11h30 à 13h00", None, None,
     "", "15h00 à 16h30", None, None, "", "17h00 à 18h30", None, None, "", None],
    ["Lundi"] + [""] * 19 + ["L", ""],
    [None, "", "", None, "", "", None, None, "", "", None, None, "", "", None, None, "", "", None, None, "undi", ""],
    [None, "", "", None, None, "", None, None, None, "", None, None, None, "", None, None, None, "", None, None, None, None],
    ["10 qq"] + [None] * 21,
    ["Mardi", "PAV4124", "TP", "Lab 6", "", "CNM410", "TD", "Lab6", "", "CNM410", "TP", "Lab6", "",
     "CNM410", "TP", "Lab6", "", "", "", "", "M", ""],
    [None, "Dév Mobile - G3/G4", "", None, "", "Réseaux avancés et sécurité", None, None, "",
     "Réseaux avancés et sécurité", None, None, "", "Réseaux avancés et sécurité", None, None, "", "",
     None, None, "ardi", ""],
    [None, "Salem/ML M’Bedah", "", None, None, "Yahjebouha", None, None, None, "Yahjebouha", None, None,
     None, "Yahjebouha", None, None, None, "", None, None, None, None],
    ["5 5 5", None, None, None, None, None, None, None, None, None, None, "", "", None, None, None, None,
     "15", None, None, "", None],
    ["Samedi"] + [""] * 19 + ["Sa", ""],
]


def test_matrice_reelle_extrait_les_quatre_seances_du_mardi():
    sessions = sessions_from_matrix(REAL_MATRIX)
    assert len(sessions) == 4
    assert all(s.day == "Tuesday" for s in sessions)
    assert [s.start_time for s in sessions] == ["08:00", "09:45", "11:30", "15:00"]
    assert [s.end_time for s in sessions] == ["09:30", "11:15", "13:00", "16:30"]

    first = sessions[0]
    assert first.name == "PAV4124 — Dév Mobile - G3/G4 (TP)"
    assert first.teacher == "Salem/ML M’Bedah"
    assert first.room == "Lab 6"

    second = sessions[1]
    assert second.name == "CNM410 — Réseaux avancés et sécurité (TD)"
    assert second.teacher == "Yahjebouha"
    assert second.room == "Lab6"


def test_matrice_reelle_ignore_lundi_et_samedi_vides():
    sessions = sessions_from_matrix(REAL_MATRIX)
    assert not any(s.day in ("Monday", "Saturday") for s in sessions)


def test_matrice_reelle_ignore_les_lignes_parasites():
    # "10 qq" et "5 5 5" apparaissent dans la matrice reelle hors de tout
    # bloc jour valide : elles ne doivent produire aucune seance ni erreur.
    sessions = sessions_from_matrix(REAL_MATRIX)
    assert all("qq" not in s.name and "5 5" not in s.name for s in sessions)


def test_sans_entete_horaire_leve_une_erreur():
    matrix = [["Lundi", "", "", ""]]
    with pytest.raises(GridPdfParseError):
        sessions_from_matrix(matrix)


def test_creneau_vide_est_ignore():
    matrix = [
        ["", "08h00 à 9H30", None, None],
        ["Lundi", "", "", ""],
        [None, "", "", ""],
        [None, "", "", ""],
    ]
    assert sessions_from_matrix(matrix) == []


def test_case_sans_code_utilise_uniquement_intitule():
    matrix = [
        ["", "08h00 à 9H30", None, None],
        ["Lundi", "", "TP", "Lab 1"],
        [None, "Sport", "", ""],
        [None, "Coach Dupont", "", ""],
    ]
    sessions = sessions_from_matrix(matrix)
    assert len(sessions) == 1
    assert sessions[0].name == "Sport (TP)"
    assert sessions[0].teacher == "Coach Dupont"
    assert sessions[0].room == "Lab 1"


def test_jour_insensible_a_la_casse():
    matrix = [
        ["", "08h00 à 9H30", None, None],
        ["  MARDI  ", "MATH101", "TD", "B2"],
        [None, "Algebre", "", ""],
        [None, "Prof X", "", ""],
    ]
    sessions = sessions_from_matrix(matrix)
    assert len(sessions) == 1
    assert sessions[0].day == "Tuesday"
