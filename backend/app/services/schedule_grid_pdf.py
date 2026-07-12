"""
Extraction de l'emploi du temps depuis un PDF "grille" (une seule page par
semaine, jours en lignes x creneaux horaires fixes en colonnes, comme le
gabarit SupNum : chaque case occupe 3 lignes -- code/type/salle, intitule,
enseignant).

Le PDF n'a pas de notion de cellule comme un tableur : on reconstruit la
grille via `pdfplumber`, qui detecte le tableau borde et renvoie une matrice
de texte. Le nom du jour n'apparait que sur la premiere des 3 lignes de son
bloc (le reste de la cellule fusionnee est vide) : on ancre donc le parsing
sur les libellés de jour trouvés en premiere colonne plutot que sur des
indices de ligne fixes, ce qui tolere les lignes d'espacement ou de
metadonnees parasites qui se glissent dans le tableau detecte (observe sur
un export reel : lignes "10 qq", "#REF!", etc. issues de cellules d'aide au
calcul du gabarit d'origine, hors de tout bloc jour donc ignorees).
"""
import io
import re
from dataclasses import dataclass

import pdfplumber

_DAY_ALIASES = {
    "lundi": "Monday",
    "mardi": "Tuesday",
    "mercredi": "Wednesday",
    "jeudi": "Thursday",
    "vendredi": "Friday",
    "samedi": "Saturday",
    "dimanche": "Sunday",
}

# "08h00 à 9H30" / "8h00 a 9h30" -> ("08:00", "09:30").
_TIME_RANGE_RE = re.compile(r"(\d{1,2})[hH](\d{2})\s*[aà]\s*(\d{1,2})[hH](\d{2})")


class GridPdfParseError(Exception):
    """Le PDF ne correspond pas au gabarit attendu (pas de tableau, pas d'horaires reconnus)."""


@dataclass
class GridSession:
    name: str
    teacher: str
    room: str
    day: str
    start_time: str
    end_time: str


def _clean(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _cell(row: list, col: int) -> str:
    return _clean(row[col]) if col < len(row) else ""


def _parse_time_range(text: str) -> tuple[str, str] | None:
    match = _TIME_RANGE_RE.search(text)
    if not match:
        return None
    start_h, start_m, end_h, end_m = match.groups()
    return f"{int(start_h):02d}:{start_m}", f"{int(end_h):02d}:{end_m}"


def _find_time_slot_columns(matrix: list[list]) -> dict[int, tuple[str, str]]:
    """Repere la ligne d'en-tete et renvoie {colonne: (heure_debut, heure_fin)}."""
    for row in matrix:
        slots: dict[int, tuple[str, str]] = {}
        for col_idx, cell in enumerate(row):
            parsed = _parse_time_range(_clean(cell))
            if parsed:
                slots[col_idx] = parsed
        if slots:
            return slots
    return {}


def sessions_from_matrix(matrix: list[list]) -> list[GridSession]:
    """
    Reconstruit les seances a partir de la matrice de texte extraite du
    tableau PDF. Fonction pure (pas d'IO) pour rester testable avec une
    matrice litterale.
    """
    time_slots = _find_time_slot_columns(matrix)
    if not time_slots:
        raise GridPdfParseError(
            "Aucune plage horaire reconnue dans le PDF (format attendu : \"8h00 a 9h30\")."
        )
    slot_columns = sorted(time_slots)

    sessions: list[GridSession] = []
    row_idx = 0
    total_rows = len(matrix)
    while row_idx < total_rows:
        label = _cell(matrix[row_idx], 0).lower()
        day = _DAY_ALIASES.get(label)
        if day is None:
            row_idx += 1
            continue

        code_row = matrix[row_idx]
        name_row = matrix[row_idx + 1] if row_idx + 1 < total_rows else []
        teacher_row = matrix[row_idx + 2] if row_idx + 2 < total_rows else []

        for slot_col in slot_columns:
            start_time, end_time = time_slots[slot_col]
            code = _cell(code_row, slot_col)
            course_type = _cell(code_row, slot_col + 1)
            room = _cell(code_row, slot_col + 2)
            title = _cell(name_row, slot_col)
            teacher = _cell(teacher_row, slot_col)

            if not code and not title:
                continue  # creneau vide ce jour-la

            name = f"{code} — {title}" if code and title else (title or code)
            if course_type:
                name = f"{name} ({course_type})"

            sessions.append(
                GridSession(
                    name=name,
                    teacher=teacher or "Unassigned",
                    room=room or "TBD",
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                )
            )

        row_idx += 3  # passe les 3 lignes de ce bloc jour ; la ligne suivante est re-scannee

    return sessions


def extract_sessions_from_pdf(content: bytes) -> list[GridSession]:
    """Ouvre le PDF, detecte le tableau borde de chaque page, et concatene les seances trouvees."""
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            sessions: list[GridSession] = []
            found_any_table = False
            for page in pdf.pages:
                for table in page.find_tables():
                    found_any_table = True
                    sessions.extend(sessions_from_matrix(table.extract()))
    except GridPdfParseError:
        raise
    except Exception as exc:  # pdfplumber/pypdfium2 peuvent lever divers types selon le fichier
        raise GridPdfParseError("PDF illisible ou corrompu.") from exc

    if not found_any_table:
        raise GridPdfParseError("Aucun tableau borde detecte dans le PDF.")
    return sessions
