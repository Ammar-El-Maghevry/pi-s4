"""
Import en masse de l'emploi du temps couvrant une semaine complete, depuis :
- un fichier CSV ou Excel (.xlsx), une ligne = une seance ; ou
- un PDF "grille" (gabarit SupNum : jours en lignes x creneaux horaires en
  colonnes, voir `app/services/schedule_grid_pdf.py`).

Colonnes CSV/XLSX attendues : "name", "teacher", "room", "day", "start_time",
"end_time" (obligatoires), "class_name", "check_in_offset_minutes",
"check_out_offset_minutes" (optionnelles, alias francais/anglais tolérés,
voir `_HEADER_ALIASES`). Le PDF grille produit directement ces memes champs
(sans class_name ni fenetres de pointage, qui prennent leurs valeurs par
defaut) : les deux sources convergent vers le meme traitement par ligne.

Seuls name/start_time/end_time/class_name sont persistes cote backend (voir
`app/models/schedule.py`) ; teacher/room/day/fenetres de pointage restent
geres cote frontend (localStorage), exactement comme pour la creation
manuelle d'un "class plan" (voir frontend/src/api/schedules.ts). Ce module
renvoie donc, pour chaque seance creee, l'integralite de la ligne source :
c'est au frontend de persister ces "extras" localement.
"""
from dataclasses import dataclass, field
from datetime import datetime, time

from sqlalchemy.orm import Session

from app.crud import schedule as crud_schedule
from app.schemas.schedule import ScheduleCreate
from app.services.schedule_grid_pdf import GridPdfParseError, extract_sessions_from_pdf
from app.services.spreadsheet import SpreadsheetFormatError, read_rows

_HEADER_ALIASES = {
    "name": "name",
    "session": "name",
    "séance": "name",
    "seance": "name",
    "teacher": "teacher",
    "enseignant": "teacher",
    "professeur": "teacher",
    "room": "room",
    "salle": "room",
    "day": "day",
    "jour": "day",
    "start_time": "start_time",
    "start": "start_time",
    "heure_debut": "start_time",
    "end_time": "end_time",
    "end": "end_time",
    "heure_fin": "end_time",
    "class_name": "class_name",
    "class": "class_name",
    "classe": "class_name",
    "check_in_offset_minutes": "check_in_offset_minutes",
    "check_in": "check_in_offset_minutes",
    "check_out_offset_minutes": "check_out_offset_minutes",
    "check_out": "check_out_offset_minutes",
}

DEFAULT_CHECK_IN_OFFSET = 15
DEFAULT_CHECK_OUT_OFFSET = 15

# Fichier texte/tableur/PDF, pas de photos individuelles : une limite plus basse
# que l'import etudiants suffit (les PDF scannes restent rares sur un gabarit d'une page).
MAX_IMPORT_BYTES = 10 * 1024 * 1024  # 10 Mo


class ScheduleImportError(Exception):
    """Erreur bloquante empechant tout traitement du fichier (format, taille)."""


@dataclass
class RowError:
    row: int
    reason: str


@dataclass
class CreatedSession:
    schedule_id: int
    name: str
    teacher: str
    room: str
    day: str
    start_time: str
    end_time: str
    check_in_offset_minutes: int
    check_out_offset_minutes: int


@dataclass
class ImportResult:
    total_rows: int = 0
    created: list[CreatedSession] = field(default_factory=list)
    invalid: int = 0
    errors: list[RowError] = field(default_factory=list)


def _parse_time(value: str) -> time | None:
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None


def _parse_offset(value: str, default: int) -> int | None:
    if not value:
        return default
    try:
        return int(float(value))
    except ValueError:
        return None


def import_schedules(db: Session, content: bytes, filename: str) -> ImportResult:
    """
    Importe des seances depuis un fichier CSV/XLSX couvrant la semaine (une
    ligne par seance). Cree une ligne en base par seance valide et renvoie,
    pour chacune, teacher/room/day/fenetres de pointage a persister cote
    frontend.
    """
    if len(content) > MAX_IMPORT_BYTES:
        raise ScheduleImportError("Fichier trop volumineux (5 Mo maximum).")

    try:
        rows = read_rows(content, filename, _HEADER_ALIASES)
    except SpreadsheetFormatError as exc:
        raise ScheduleImportError(str(exc)) from exc

    result = ImportResult(total_rows=len(rows))

    for index, record in enumerate(rows, start=2):  # ligne 2 = premiere ligne de donnees (apres l'en-tete)
        name = record.get("name", "")
        teacher = record.get("teacher", "")
        room = record.get("room", "")
        day = record.get("day", "")
        start_raw = record.get("start_time", "")
        end_raw = record.get("end_time", "")

        if not all([name, teacher, room, day, start_raw, end_raw]):
            result.invalid += 1
            result.errors.append(
                RowError(row=index, reason="Champs requis manquants (name/teacher/room/day/start_time/end_time)")
            )
            continue

        start_time = _parse_time(start_raw)
        end_time = _parse_time(end_raw)
        if start_time is None or end_time is None:
            result.invalid += 1
            result.errors.append(RowError(row=index, reason="Heure invalide (attendu HH:MM)"))
            continue
        if end_time <= start_time:
            result.invalid += 1
            result.errors.append(RowError(row=index, reason="L'heure de fin doit suivre l'heure de debut"))
            continue

        check_in = _parse_offset(record.get("check_in_offset_minutes", ""), DEFAULT_CHECK_IN_OFFSET)
        check_out = _parse_offset(record.get("check_out_offset_minutes", ""), DEFAULT_CHECK_OUT_OFFSET)
        if check_in is None or check_out is None:
            result.invalid += 1
            result.errors.append(RowError(row=index, reason="Fenetre de pointage invalide (nombre attendu)"))
            continue

        schedule = crud_schedule.create_schedule(
            db,
            ScheduleCreate(
                name=name,
                start_time=start_time,
                end_time=end_time,
                class_name=record.get("class_name") or None,
            ),
        )
        result.created.append(
            CreatedSession(
                schedule_id=schedule.id,
                name=schedule.name,
                teacher=teacher,
                room=room,
                day=day,
                start_time=start_time.strftime("%H:%M"),
                end_time=end_time.strftime("%H:%M"),
                check_in_offset_minutes=check_in,
                check_out_offset_minutes=check_out,
            )
        )

    return result
