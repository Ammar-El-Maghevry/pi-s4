"""
Tests des schémas caméra (couche pure, sans base de données).

Couvre les deux points sensibles :
- le masquage des identifiants du `source_url` en lecture ;
- la validation des seuils (plage [0, 1] et present > late).
"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.enums import CrossingDirection
from app.schemas.camera import CameraCreate, CameraRead, CameraUpdate, mask_source_url


# --------------------------- Masquage source_url --------------------------- #

def test_mask_rtsp_avec_identifiants():
    masked = mask_source_url("rtsp://admin:secret@192.168.1.10:554/stream")
    assert masked == "rtsp://***:***@192.168.1.10:554/stream"
    assert "admin" not in masked and "secret" not in masked


def test_mask_source_sans_identifiants_inchangee():
    assert mask_source_url("0") == "0"
    assert mask_source_url("rtsp://192.168.1.10:554/stream") == "rtsp://192.168.1.10:554/stream"


def test_camera_read_masque_le_source_url():
    # from_attributes lit un objet ; on simule une caméra avec identifiants.
    now = datetime(2026, 3, 2, 8, 0)
    fake_camera = type(
        "FakeCamera",
        (),
        {
            "id": 1,
            "name": "Salle A",
            "location": None,
            "source_url": "rtsp://user:pass@cam.local:554/s",
            "is_active": True,
            "line_x1": None, "line_y1": None, "line_x2": None, "line_y2": None,
            "crossing_direction": CrossingDirection.TOP_TO_BOTTOM_IS_ENTRY,
            "min_crossing_frames": 3,
            "cooldown_seconds": 5,
            "present_threshold": 0.7,
            "late_threshold": 0.2,
            "face_match_threshold": 0.5,
            "created_at": now,
            "updated_at": now,
        },
    )()
    read = CameraRead.model_validate(fake_camera)
    assert read.source_url == "rtsp://***:***@cam.local:554/s"


# ------------------------------ Validation seuils -------------------------- #

def test_create_rejette_present_inferieur_a_late():
    with pytest.raises(ValidationError):
        CameraCreate(name="X", source_url="0", present_threshold=0.2, late_threshold=0.5)


def test_create_rejette_seuil_hors_plage():
    with pytest.raises(ValidationError):
        CameraCreate(name="X", source_url="0", present_threshold=1.5)


def test_create_valide_par_defaut():
    cam = CameraCreate(name="Salle A", source_url="0")
    assert cam.present_threshold > cam.late_threshold
    assert cam.crossing_direction == CrossingDirection.TOP_TO_BOTTOM_IS_ENTRY


def test_update_verifie_seuils_seulement_si_les_deux_fournis():
    # Un seul seuil fourni : pas d'erreur (comparaison impossible).
    CameraUpdate(present_threshold=0.9)
    # Les deux fournis et incohérents : erreur.
    with pytest.raises(ValidationError):
        CameraUpdate(present_threshold=0.2, late_threshold=0.6)
