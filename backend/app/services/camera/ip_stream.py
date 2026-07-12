"""
Lecture continue des cameras IP/RTSP/USB pour la reconnaissance en direct.

Miroir du modele "derniere frame" de `webrtc.py`, mais pour les flux OpenCV :
un thread lecteur par camera draine le flux en continu et ne conserve que la
frame la plus recente. La boucle de reconnaissance (`live_recognition.py`)
vient prelever cette frame a sa propre cadence, exactement comme elle le fait
pour une camera telephone.

Pourquoi un lecteur persistant plutot qu'une ouverture a chaque tick :
- ouvrir un flux RTSP coute une negociation (souvent > 1 s), inacceptable
  toutes les 3 secondes ;
- un flux RTSP non draine sert des frames en retard (tampon interne OpenCV) :
  il faut lire en continu pour que "la derniere frame" soit reellement recente.

Cycle de vie : le lecteur est cree paresseusement au premier prelevement (donc
uniquement pendant une seance active, `live_recognition` ne prelevant pas hors
seance) et s'arrete tout seul apres `_IDLE_STOP_SECONDS` sans prelevement —
aucun flux ne tourne pour rien en dehors des cours. En cas de coupure, il
retente l'ouverture avec un delai (`_RECONNECT_DELAY_SECONDS`).

Meme hypothese process-unique que `webrtc.py` : registre en memoire process-local.
"""
import logging
import threading
import time

import numpy as np

logger = logging.getLogger("app")

# Frame plus vieille que ceci = flux considere gele, on ne la sert pas
# (marquer une presence sur une image d'il y a une minute serait faux).
_STALE_FRAME_SECONDS = 10.0
# Sans prelevement pendant ce delai (seance terminee), le lecteur s'arrete.
_IDLE_STOP_SECONDS = 30.0
# Delai entre deux tentatives d'ouverture apres un echec.
_RECONNECT_DELAY_SECONDS = 5.0


def _normalize_source(source_url: str):
    """Index USB numerique ("0", "1"...) -> int ; sinon URL telle quelle (voir connection.py)."""
    return int(source_url) if source_url.strip().isdigit() else source_url


class _Reader:
    """Thread lecteur d'une camera : draine le flux, garde la derniere frame."""

    def __init__(self, camera_id: int, source_url: str):
        self.camera_id = camera_id
        self.source_url = source_url
        self._lock = threading.Lock()
        self._frame: np.ndarray | None = None
        self._frame_at = 0.0
        self._last_poll = time.monotonic()
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run, name=f"ip-camera-{camera_id}", daemon=True
        )
        self._thread.start()

    def latest_frame(self) -> np.ndarray | None:
        with self._lock:
            self._last_poll = time.monotonic()
            if self._frame is None or time.monotonic() - self._frame_at > _STALE_FRAME_SECONDS:
                return None
            return self._frame

    def stop(self) -> None:
        self._stop.set()

    @property
    def alive(self) -> bool:
        return self._thread.is_alive()

    def _idle_expired(self) -> bool:
        with self._lock:
            return time.monotonic() - self._last_poll > _IDLE_STOP_SECONDS

    def _run(self) -> None:
        import cv2  # noqa: PLC0415 — import paresseux, comme connection.py

        capture = None
        try:
            while not self._stop.is_set() and not self._idle_expired():
                if capture is None or not capture.isOpened():
                    if capture is not None:
                        capture.release()
                    capture = cv2.VideoCapture(_normalize_source(self.source_url))
                    if not capture.isOpened():
                        logger.warning(
                            "Camera IP %s : flux injoignable, nouvel essai dans %.0fs",
                            self.camera_id,
                            _RECONNECT_DELAY_SECONDS,
                        )
                        capture.release()
                        capture = None
                        if self._stop.wait(_RECONNECT_DELAY_SECONDS):
                            return
                        continue

                ok, frame = capture.read()
                if not ok or frame is None:
                    # Flux coupe : on repasse par l'ouverture au prochain tour.
                    capture.release()
                    capture = None
                    if self._stop.wait(_RECONNECT_DELAY_SECONDS):
                        return
                    continue

                with self._lock:
                    self._frame = frame
                    self._frame_at = time.monotonic()
        finally:
            if capture is not None:
                capture.release()
            logger.info("Camera IP %s : lecteur arrete", self.camera_id)


_readers: dict[int, _Reader] = {}
_registry_lock = threading.Lock()


def get_latest_frame_bgr(camera_id: int, source_url: str) -> np.ndarray | None:
    """
    Derniere frame (BGR) de la camera, ou None si le flux n'est pas (encore)
    disponible. Demarre le lecteur au premier appel ; le relance s'il s'est
    arrete (inactivite apres une seance) ou si la source a change.
    """
    if not source_url:
        return None
    with _registry_lock:
        reader = _readers.get(camera_id)
        if reader is None or not reader.alive or reader.source_url != source_url:
            if reader is not None:
                reader.stop()
            reader = _Reader(camera_id, source_url)
            _readers[camera_id] = reader
    return reader.latest_frame()


def stop_all() -> None:
    """Arrete tous les lecteurs (appele a l'arret de l'application)."""
    with _registry_lock:
        for reader in _readers.values():
            reader.stop()
        _readers.clear()
