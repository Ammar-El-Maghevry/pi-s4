"""
Couche d'accès aux données pour les caméras.

Opérations de création, lecture, liste, mise à jour et suppression. La valeur
complète de `source_url` (avec identifiants) est conservée ici ; c'est la couche
schéma qui la masque à la sortie.

Les caméras téléphone (`source_type=PHONE`) ont en plus un `webrtc_token`
généré ici. Cette couche ne ferme JAMAIS elle-même une session WebRTC en
mémoire (c'est une opération asynchrone réseau ; la boucle d'évènements
appartient au serveur ASGI, pas à ce code synchrone) : `update_camera` et
`delete_camera` renvoient l'ancien jeton à fermer, à charge pour la route
(async) d'appeler `close_phone_camera_session`.
"""
import secrets

from sqlalchemy.orm import Session

from app.models.camera import Camera
from app.models.enums import CameraSourceType
from app.schemas.camera import PHONE_SOURCE_URL_PLACEHOLDER, CameraCreate, CameraUpdate


def get_camera(db: Session, camera_pk: int) -> Camera | None:
    """Récupère une caméra par sa clé primaire."""
    return db.query(Camera).filter(Camera.id == camera_pk).first()


def get_camera_by_token(db: Session, token: str) -> Camera | None:
    """Récupère une caméra téléphone par son jeton d'appairage WebRTC."""
    return db.query(Camera).filter(Camera.webrtc_token == token).first()


def list_cameras(db: Session, skip: int = 0, limit: int = 100) -> list[Camera]:
    """Liste les caméras, ordonnées par nom."""
    return db.query(Camera).order_by(Camera.name).offset(skip).limit(limit).all()


def create_camera(db: Session, data: CameraCreate) -> Camera:
    """Crée une nouvelle caméra (génère un jeton WebRTC pour une caméra téléphone)."""
    fields = data.model_dump()
    if fields["source_type"] == CameraSourceType.PHONE:
        fields["webrtc_token"] = secrets.token_urlsafe(24)
        fields["source_url"] = PHONE_SOURCE_URL_PLACEHOLDER
    camera = Camera(**fields)
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


def update_camera(db: Session, camera: Camera, data: CameraUpdate) -> tuple[Camera, str | None]:
    """
    Met à jour une caméra avec uniquement les champs fournis.

    Renvoie la caméra mise à jour et, le cas échéant, l'ancien jeton WebRTC
    dont la session en mémoire doit être fermée par l'appelant.
    """
    updates = data.model_dump(exclude_unset=True)

    effective_source_type = updates.get("source_type", camera.source_type)
    effective_source_url = (updates.get("source_url", camera.source_url) or "").strip()

    if effective_source_type == CameraSourceType.IP_CAMERA and (
        not effective_source_url or effective_source_url == PHONE_SOURCE_URL_PLACEHOLDER
    ):
        raise ValueError("source_url est obligatoire pour une camera IP")

    for field, value in updates.items():
        setattr(camera, field, value)

    stale_token: str | None = None
    if camera.source_type == CameraSourceType.PHONE:
        # Toujours forcer le placeholder : le client peut renvoyer un
        # `source_url` perimé (ex. le formulaire d'edition l'envoie a vide),
        # et un nouveau jeton n'est genere que la premiere fois.
        if not camera.webrtc_token:
            camera.webrtc_token = secrets.token_urlsafe(24)
        camera.source_url = PHONE_SOURCE_URL_PLACEHOLDER
    elif camera.webrtc_token:
        stale_token = camera.webrtc_token
        camera.webrtc_token = None

    db.commit()
    db.refresh(camera)
    return camera, stale_token


def delete_camera(db: Session, camera: Camera) -> str | None:
    """Supprime une caméra. Renvoie son jeton WebRTC (le cas échéant) à fermer."""
    token = camera.webrtc_token
    db.delete(camera)
    db.commit()
    return token
