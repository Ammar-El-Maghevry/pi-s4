"""
Tests du lecteur de flux IP (`services/camera/ip_stream.py`) avec un faux
OpenCV injecte : verifie le cycle de vie du lecteur (demarrage paresseux,
frame servie, redemarrage si la source change, arret global) sans camera
reelle.
"""
import sys
import time
import types

import numpy as np
import pytest

from app.services.camera import ip_stream


class FakeCapture:
    """Simule cv2.VideoCapture : sert une frame constante, comptabilise release()."""

    released_count = 0

    def __init__(self, source):
        self.source = source
        self._opened = source != "rtsp://unreachable"

    def isOpened(self):
        return self._opened

    def read(self):
        if not self._opened:
            return False, None
        time.sleep(0.01)  # simule la cadence du flux, evite une boucle chauffante
        return True, np.zeros((4, 4, 3), dtype=np.uint8)

    def release(self):
        FakeCapture.released_count += 1


@pytest.fixture(autouse=True)
def fake_cv2(monkeypatch):
    module = types.SimpleNamespace(VideoCapture=FakeCapture)
    monkeypatch.setitem(sys.modules, "cv2", module)
    yield
    ip_stream.stop_all()


def _wait_for_frame(camera_id: int, url: str, timeout: float = 2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        frame = ip_stream.get_latest_frame_bgr(camera_id, url)
        if frame is not None:
            return frame
        time.sleep(0.02)
    return None


def test_normalize_source_index_usb_et_url():
    assert ip_stream._normalize_source("0") == 0
    assert ip_stream._normalize_source(" 2 ") == 2
    url = "rtsp://user:pass@cam.local:554/s"
    assert ip_stream._normalize_source(url) == url


def test_premier_appel_demarre_le_lecteur_et_sert_une_frame():
    frame = _wait_for_frame(1, "rtsp://cam.local/stream")
    assert frame is not None
    assert frame.shape == (4, 4, 3)


def test_source_vide_ne_demarre_rien():
    assert ip_stream.get_latest_frame_bgr(2, "") is None


def test_flux_injoignable_sert_none_sans_lever():
    assert ip_stream.get_latest_frame_bgr(3, "rtsp://unreachable") is None


def test_changement_de_source_redemarre_le_lecteur():
    assert _wait_for_frame(4, "rtsp://old.local/stream") is not None
    old_reader = ip_stream._readers[4]
    _wait_for_frame(4, "rtsp://new.local/stream")
    assert ip_stream._readers[4] is not old_reader
    assert ip_stream._readers[4].source_url == "rtsp://new.local/stream"


def test_stop_all_vide_le_registre():
    _wait_for_frame(5, "rtsp://cam.local/stream")
    assert ip_stream._readers
    ip_stream.stop_all()
    assert not ip_stream._readers
