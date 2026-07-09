"""
Boucle de reconnaissance en direct.

À intervalle fixe, pour chaque caméra téléphone connectée et actuellement
assignée à une séance en cours (heure courante dans le créneau), on prélève sa
dernière frame reçue, on y détecte les visages, on les compare aux étudiants
enrôlés et on enregistre une ENTRÉE pour tout étudiant reconnu — une seule par
étudiant par séance (voir `_marked_sessions`).

Un visage non reconnu comme étudiant est ensuite comparé aux enseignants
enrôlés : un enseignant n'étant pas rattaché à une classe (il n'a donc pas de
notion d'entrée/sortie par séance comme un étudiant), sa présence est un simple
drapeau présent/absent du jour (`teacher_attendance`), positionné dès qu'il est
reconnu par la caméra d'une séance en cours (voir `_marked_teachers`).

Dès que le créneau d'une séance se termine, on enregistre aussitôt une SORTIE
pour chaque étudiant ayant un intervalle encore ouvert avant la fin de ce
créneau (`_close_finished_sessions`, dérivé des évènements en base — pas d'un
cache mémoire — pour rester correct même si le process redémarre entre la fin
de la séance et le prochain tick). C'est nécessaire : `intervals.py` traite une
entrée sans sortie comme une présence qui court jusqu'à la fin de N'IMPORTE
QUELLE fenêtre évaluée ensuite — sans cette clôture, un étudiant entré en
séance 1 apparaîtrait automatiquement présent à toutes les séances suivantes de
la journée.

Hypothèse simplificatrice : un seul process uvicorn (déjà posée par
`services/camera/webrtc.py`) donc des dicts/sets en mémoire process-local
suffisent (`_marked_sessions`, `_closed_sessions`).

Le reste — détection/tracking multi-visages sophistiqués, franchissement de
ligne — n'existe pas.
"""
import asyncio
import logging
from contextlib import suppress
from datetime import date, datetime

from app.crud import attendance_event as crud_event
from app.crud import camera as crud_camera
from app.crud import schedule as crud_schedule
from app.crud import student as crud_student
from app.crud import teacher as crud_teacher
from app.database import SessionLocal
from app.models.camera import Camera
from app.models.enums import CameraSourceType, EventType, SessionType
from app.schemas.attendance_event import AttendanceEventCreate
from app.services.ai.face_embedding import extract_all_face_embeddings, match_student
from app.services.attendance.engine import session_window
from app.services.attendance.intervals import _naive, build_intervals
from app.services.attendance.service import compute_student_date
from app.services.camera.webrtc import get_latest_frame_bgr

logger = logging.getLogger("app")

# Cadence du pipeline : assez rapide pour marquer présent tôt dans la séance,
# assez lent pour ne pas saturer un CPU unique avec de l'inférence InsightFace.
_TICK_SECONDS = 3.0

# (student_id, schedule_id) -> jour où l'ENTRÉE a été enregistrée (évite le spam).
_marked_sessions: dict[tuple[int, int], date] = {}
# (schedule_id, jour) déjà clôturés (SORTIE écrite pour tous les présents).
_closed_sessions: set[tuple[int, date]] = set()
# teacher_id -> jour où sa présence a déjà été positionnée (évite le spam).
_marked_teachers: dict[int, date] = {}

_task: asyncio.Task | None = None


def _active_session(db, camera_id: int, now: datetime):
    """Séance en cours (heure courante dans le créneau) assignée à cette caméra, s'il y en a une."""
    now_time = now.time()
    for schedule in crud_schedule.list_schedules(db):
        if (
            schedule.session_type == SessionType.SESSION
            and schedule.camera_id == camera_id
            and schedule.start_time <= now_time <= schedule.end_time
        ):
            return schedule
    return None


def _process_camera(db, camera: Camera, now: datetime) -> None:
    if camera.source_type != CameraSourceType.PHONE or not camera.is_active or not camera.webrtc_token:
        return
    schedule = _active_session(db, camera.id, now)
    if schedule is None:
        return

    frame = get_latest_frame_bgr(camera.webrtc_token)
    if frame is None:
        return

    try:
        faces = extract_all_face_embeddings(frame)
    except Exception:
        logger.exception("Echec de la reconnaissance en direct pour la camera %s", camera.id)
        return
    if not faces:
        return

    candidates = crud_student.list_face_candidates(db, class_name=schedule.class_name)
    if not candidates:
        return

    today = now.date()
    for face in faces:
        match = match_student(face.embedding, candidates, threshold=camera.face_match_threshold)
        if match is None:
            continue
        student_id, score = match
        key = (student_id, schedule.id)
        if _marked_sessions.get(key) == today:
            continue

        crud_event.create_event(
            db,
            AttendanceEventCreate(
                student_id=student_id,
                event_type=EventType.ENTRY,
                confidence=score,
                camera_id=str(camera.id),
            ),
        )
        _marked_sessions[key] = today
        compute_student_date(db, student_id, today)
        db.commit()


def _close_finished_sessions(db, now: datetime) -> None:
    """Ecrit une SORTIE pour chaque etudiant marque present a une seance dont le creneau vient de se terminer."""
    today = now.date()
    now_time = now.time()
    for schedule in crud_schedule.list_schedules(db):
        if schedule.session_type != SessionType.SESSION or schedule.end_time > now_time:
            continue
        close_key = (schedule.id, today)
        if close_key in _closed_sessions:
            continue
        _closed_sessions.add(close_key)

        # Dérivé de la base plutôt que de `_marked_sessions` : un redémarrage du
        # process entre la fin de la séance et le prochain tick effacerait ce
        # cache mémoire, laissant un étudiant réellement entré "ouvert" pour de
        # bon (voir la présence qui, sinon, fuiterait vers les séances
        # suivantes). Idempotent : si déjà clôturé, plus aucun intervalle
        # ouvert n'est trouvé et cette passe ne fait rien.
        _, window_end = session_window(today, schedule.start_time, schedule.end_time)
        for student_id in crud_event.distinct_student_ids_with_events_on_date(db, today):
            events = crud_event.get_events_for_student_on_date(db, student_id, today)
            has_open_before_window_end = any(
                interval.end is None and _naive(interval.start) < window_end
                for interval in build_intervals(events)
            )
            if not has_open_before_window_end:
                continue
            crud_event.create_event(
                db,
                AttendanceEventCreate(student_id=student_id, event_type=EventType.EXIT),
            )
            compute_student_date(db, student_id, today)
            db.commit()


def _tick() -> None:
    db = SessionLocal()
    try:
        now = datetime.now()
        for camera in crud_camera.list_cameras(db, limit=500):
            _process_camera(db, camera, now)
        _close_finished_sessions(db, now)
    finally:
        db.close()


async def _loop_forever() -> None:
    while True:
        with suppress(Exception):
            await asyncio.to_thread(_tick)
        await asyncio.sleep(_TICK_SECONDS)


def start() -> None:
    """Démarre la boucle de reconnaissance (appelé au démarrage de l'application)."""
    global _task
    if _task is None:
        _task = asyncio.create_task(_loop_forever())


async def stop() -> None:
    """Arrête la boucle de reconnaissance (appelé à l'arrêt de l'application)."""
    global _task
    if _task is not None:
        _task.cancel()
        with suppress(asyncio.CancelledError):
            await _task
        _task = None
