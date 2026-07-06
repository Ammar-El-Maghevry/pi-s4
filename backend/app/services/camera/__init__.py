"""
Paquet des services liés aux caméras.

`connection` teste une caméra IP/RTSP/USB (une frame via OpenCV) ; `webrtc`
reçoit en direct le flux d'un téléphone (aiortc) et expose son statut avec la
même forme de résultat. Le pipeline d'inférence temps réel (détection,
suivi, franchissement de ligne) reste un module futur séparé.
"""
from app.services.camera.connection import test_camera_connection
from app.services.camera.webrtc import get_status as get_phone_camera_status
from app.services.camera.webrtc import handle_offer as handle_phone_camera_offer
from app.services.camera.webrtc import close_session as close_phone_camera_session
from app.services.camera.webrtc import shutdown_all as shutdown_phone_camera_sessions
from app.services.camera.webrtc import start_reaper as start_phone_camera_reaper
from app.services.camera.webrtc import stop_reaper as stop_phone_camera_reaper

__all__ = [
    "test_camera_connection",
    "get_phone_camera_status",
    "handle_phone_camera_offer",
    "close_phone_camera_session",
    "shutdown_phone_camera_sessions",
    "start_phone_camera_reaper",
    "stop_phone_camera_reaper",
]
