"""
Réception d'un flux vidéo de téléphone via WebRTC (aiortc).

Un téléphone ouvre la page publique /phone-camera/<token> dans son propre
navigateur, capture sa caméra (getUserMedia) et envoie une offre SDP à
`handle_offer`. Ce module maintient, en mémoire, une session par jeton : la
connexion `RTCPeerConnection` et la taille/l'horodatage de la dernière frame
reçue. On ne matérialise PAS les pixels de chaque frame en tableau numpy ici :
rien ne les consomme aujourd'hui (seul un statut de connexion est exposé), et
décoder ~20 frames/seconde pour ne garder que la dernière serait du travail
jeté. Un futur pipeline de détection pourra le faire à sa propre cadence.

Hypothèse simplificatrice assumée : un seul processus uvicorn (pas de
`--workers`, confirmé dans `docker-entrypoint.sh`/`Dockerfile`) donc un
dictionnaire en mémoire du process suffit ; aucune coordination multi-process
n'est nécessaire. Si le déploiement passe un jour en multi-process/instances,
ce module devra être remplacé par un stockage partagé (Redis, etc.).

aiortc est importé paresseusement (jamais au démarrage de l'API), comme cv2
dans `connection.py`.
"""
import asyncio
from collections import defaultdict
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.services.camera.connection import ConnectionResult

# Au-delà de ce délai sans nouvelle frame, la session est considérée inactive
# (le téléphone a probablement perdu la connexion ou verrouillé son écran).
_STALE_FRAME_AFTER = timedelta(seconds=5)
# Nettoyage périodique des sessions abandonnées (ex. le navigateur du
# téléphone est tué sans jamais notifier de changement d'état de connexion).
_REAP_INTERVAL = timedelta(seconds=30)
_REAP_AFTER = _STALE_FRAME_AFTER * 4

# Borne le temps de fermeture d'une session (teardown ICE/DTLS peut, en de
# rares cas, ne jamais se terminer proprement) pour que `close_session` rende
# toujours la main.
_CLOSE_TIMEOUT_SECONDS = 5


@dataclass
class _PhoneCameraSession:
    pc: object  # aiortc.RTCPeerConnection (typé `object` pour ne pas importer aiortc au chargement)
    last_frame_size: tuple[int, int] | None = None  # (largeur, hauteur)
    last_frame_at: datetime | None = None
    # Dernière frame brute (av.VideoFrame), gardée telle quelle : le décodage en
    # tableau BGR (coûteux) n'a lieu qu'à la demande, dans `get_latest_frame_bgr`,
    # à la cadence du pipeline de reconnaissance plutôt qu'a chaque frame reçue.
    last_av_frame: object | None = None
    track_task: asyncio.Task | None = None


_sessions: dict[str, _PhoneCameraSession] = {}
# Une session par jeton à la fois : sérialise les offres concurrentes/rejouées
# pour le même jeton afin qu'aucune RTCPeerConnection ne reste orpheline.
_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
_reaper_task: asyncio.Task | None = None


async def handle_offer(token: str, sdp: str, sdp_type: str) -> tuple[str, str]:
    """
    Traite l'offre SDP d'un téléphone : ouvre une nouvelle session pour ce
    jeton (referme l'ancienne s'il y en avait une) et renvoie la réponse SDP.
    """
    from aiortc import RTCPeerConnection, RTCSessionDescription  # noqa: PLC0415

    async with _locks[token]:
        await close_session(token)

        pc = RTCPeerConnection()
        session = _PhoneCameraSession(pc=pc)
        _sessions[token] = session

        @pc.on("track")
        def on_track(track):
            if track.kind == "video":
                session.track_task = asyncio.create_task(_consume_track(token, track))

        @pc.on("connectionstatechange")
        async def on_state_change():
            if pc.connectionState in ("failed", "closed", "disconnected"):
                await close_session(token)

        await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type=sdp_type))
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return pc.localDescription.sdp, pc.localDescription.type


async def _consume_track(token: str, track) -> None:
    """Lit les frames du téléphone en continu ; ne garde que taille + horodatage."""
    from aiortc.mediastreams import MediaStreamError  # noqa: PLC0415

    try:
        while True:
            frame = await track.recv()
            session = _sessions.get(token)
            if session is None:
                return
            session.last_frame_size = (frame.width, frame.height)
            session.last_frame_at = datetime.now(timezone.utc)
            session.last_av_frame = frame
    except (MediaStreamError, asyncio.CancelledError):
        return


async def close_session(token: str) -> None:
    """Ferme (si elle existe) la session WebRTC associée à ce jeton."""
    session = _sessions.pop(token, None)
    if session is None:
        return
    if session.track_task is not None:
        session.track_task.cancel()
        with suppress(asyncio.CancelledError):
            await session.track_task
    with suppress(asyncio.TimeoutError):
        await asyncio.wait_for(session.pc.close(), timeout=_CLOSE_TIMEOUT_SECONDS)


async def shutdown_all() -> None:
    """Ferme toutes les sessions actives (appelé à l'arrêt de l'application)."""
    for token in list(_sessions):
        await close_session(token)


async def _reap_stale_sessions_forever() -> None:
    """Ferme périodiquement les sessions abandonnées (voir `_REAP_AFTER`)."""
    while True:
        await asyncio.sleep(_REAP_INTERVAL.total_seconds())
        now = datetime.now(timezone.utc)
        for token, session in list(_sessions.items()):
            reference = session.last_frame_at
            if reference is None:
                continue
            if now - reference > _REAP_AFTER:
                await close_session(token)


def start_reaper() -> None:
    """Démarre le nettoyage périodique (appelé au démarrage de l'application)."""
    global _reaper_task
    if _reaper_task is None:
        _reaper_task = asyncio.create_task(_reap_stale_sessions_forever())


async def stop_reaper() -> None:
    """Arrête le nettoyage périodique (appelé à l'arrêt de l'application)."""
    global _reaper_task
    if _reaper_task is not None:
        _reaper_task.cancel()
        with suppress(asyncio.CancelledError):
            await _reaper_task
        _reaper_task = None


def get_latest_frame_bgr(token: str):
    """
    Décode la dernière frame reçue de ce téléphone en tableau OpenCV (BGR).

    Renvoie `None` si aucun téléphone n'est connecté ou si la dernière frame
    date de plus de `_STALE_FRAME_AFTER` (téléphone probablement déconnecté).
    Appelé depuis le pipeline de reconnaissance en direct, à sa propre cadence.
    """
    session = _sessions.get(token)
    if session is None or session.last_av_frame is None or session.last_frame_at is None:
        return None
    if datetime.now(timezone.utc) - session.last_frame_at > _STALE_FRAME_AFTER:
        return None
    return session.last_av_frame.to_ndarray(format="bgr24")


def get_status(token: str | None) -> ConnectionResult:
    """
    Statut courant d'une caméra téléphone, dans le même format que
    `test_camera_connection` (pour un affichage unifié côté API/UI).
    """
    if not token:
        return ConnectionResult(False, "Aucun jeton WebRTC configure pour cette camera.")

    session = _sessions.get(token)
    if session is None:
        return ConnectionResult(False, "Aucun telephone connecte pour le moment.")

    if session.last_frame_size is None or session.last_frame_at is None:
        return ConnectionResult(True, "Telephone connecte, en attente de la premiere image.")

    if datetime.now(timezone.utc) - session.last_frame_at > _STALE_FRAME_AFTER:
        return ConnectionResult(False, "Session inactive (aucune image recente du telephone).")

    width, height = session.last_frame_size
    return ConnectionResult(True, "Flux telephone actif.", width=width, height=height)
