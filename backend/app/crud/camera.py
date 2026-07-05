"""
Couche d'accès aux données pour les caméras.

Opérations de création, lecture, liste, mise à jour et suppression. La valeur
complète de `source_url` (avec identifiants) est conservée ici ; c'est la couche
schéma qui la masque à la sortie.
"""
from sqlalchemy.orm import Session

from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate


def get_camera(db: Session, camera_pk: int) -> Camera | None:
    """Récupère une caméra par sa clé primaire."""
    return db.query(Camera).filter(Camera.id == camera_pk).first()


def list_cameras(db: Session, skip: int = 0, limit: int = 100) -> list[Camera]:
    """Liste les caméras, ordonnées par nom."""
    return db.query(Camera).order_by(Camera.name).offset(skip).limit(limit).all()


def create_camera(db: Session, data: CameraCreate) -> Camera:
    """Crée une nouvelle caméra."""
    camera = Camera(**data.model_dump())
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


def update_camera(db: Session, camera: Camera, data: CameraUpdate) -> Camera:
    """Met à jour une caméra avec uniquement les champs fournis."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(camera, field, value)
    db.commit()
    db.refresh(camera)
    return camera


def delete_camera(db: Session, camera: Camera) -> None:
    """Supprime une caméra."""
    db.delete(camera)
    db.commit()
