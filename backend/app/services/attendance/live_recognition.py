"""
Boucle de reconnaissance en direct.

À intervalle fixe, pour chaque caméra téléphone connectée et actuellement
assignée à une séance en cours (heure courante dans le créneau), on prélève sa
dernière frame reçue, on y détecte les visages, on les compare aux étudiants
enrôlés et on enregistre une ENTRÉE pour tout étudiant reconnu.

Une seule ENTRÉE suffit par étudiant par jour : `services/attendance` traite un
intervalle sans SORTIE comme une présence qui court jusqu'à la fin du créneau
(voir `intervals.py`), donc pas besoin de suivre la personne en continu pour la
compter présente sur toute la séance. Un cache mémoire (`_marked_today`) évite
de ré-insérer un évènement à chaque cycle pour la même personne.

Hypothèse simplificatrice : un seul process uvicorn (déjà posée par
`services/camera/webrtc.py`) donc un dict en mémoire process-local suffit.

Le reste — détection/tracking multi-visages sophistiqués, franchissement de
ligne, empreinte pour les enseignants — n'existe pas : seuls les étudiants ont
un embedding enrôlé aujourd'hui (voir `app/models/student.py`).
"""
import asyncio
import logging
from contextlib import suppress
from datetime import date, datetime

from app.crud import attendance_event as crud_event
from app.crud import camera as crud_camera
from app.crud import schedule as crud_schedule
from app.crud import student as crud_student
from app.database import SessionLocal
from app.models.camera import Camera
from app.models.enums import CameraSourceType, EventType, SessionType
from app.schemas.attendance_event import AttendanceEventCreate
from app.services.ai.face_embedding import extract_all_face_embeddings, match_student
from app.services.attendance.service import compute_student_date
from app.services.camera.webrtc import get_latest_frame_bgr

logger = logging.getLogger("app")

# Cadence du pipeline : assez rapide pour marquer présent tôt dans la séance,
# assez lent pour ne pas saturer un CPU unique avec de l'inférence InsightFace.
_TICK_SECONDS = 3.0

# student_id -> dernier jour où une ENTRÉE a été enregistrée (évite le spam).
_marked_today: dict[int, date] = {}

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
    if _active_session(db, camera.id, now) is None:
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

    candidates = crud_student.list_face_candidates(db)
    if not candidates:
        return

    today = now.date()
    for face in faces:
        match = match_student(face.embedding, candidates, threshold=camera.face_match_threshold)
        if match is None:
            continue
        student_id, score = match
        if _marked_today.get(student_id) == today:
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
        _marked_today[student_id] = today
        compute_student_date(db, student_id, today)
        db.commit()


def _tick() -> None:
    db = SessionLocal()
    try:
        now = datetime.now()
        for camera in crud_camera.list_cameras(db, limit=500):
            _process_camera(db, camera, now)
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
