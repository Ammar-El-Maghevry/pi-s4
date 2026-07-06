"""
Modèle des caméras.

Une ligne = une caméra installée dans une salle. Ce modèle permet à
l'administrateur de configurer, depuis l'application (sans toucher au code ni au
.env), la connexion au flux et les paramètres de détection : ligne de
franchissement, seuils de présence et de reconnaissance.

Conçu pour être extensible à plusieurs salles (chaque caméra a son propre
`source_url` et ses propres réglages). Le champ `attendance_events.camera_id`
référence logiquement le nom / identifiant de la caméra.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import CameraSourceType, CrossingDirection


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Nom lisible (ex. « Salle A ») et emplacement optionnel.
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Origine du flux : caméra IP/RTSP/USB classique, ou téléphone (WebRTC).
    source_type: Mapped[CameraSourceType] = mapped_column(
        Enum(CameraSourceType), default=CameraSourceType.IP_CAMERA, nullable=False
    )
    # Source du flux : URL RTSP (rtsp://user:pass@host:554/stream) ou index USB.
    # La valeur complète (avec identifiants) reste en base pour le service caméra ;
    # elle n'est JAMAIS renvoyée en clair par l'API (voir le schéma de lecture).
    # Pour une caméra téléphone, contient un simple placeholder (non utilisé) :
    # le flux réel vit en mémoire, indexé par `webrtc_token`.
    source_url: Mapped[str] = mapped_column(String(512), nullable=False)
    # Jeton d'appairage unique du lien /phone-camera/<token> (caméras téléphone uniquement).
    webrtc_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Ligne de franchissement virtuelle (coordonnées en pixels) ---
    # Nullable : une caméra peut être créée avant que la ligne ne soit tracée.
    line_x1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_y1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_x2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_y2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    crossing_direction: Mapped[CrossingDirection] = mapped_column(
        Enum(CrossingDirection),
        default=CrossingDirection.TOP_TO_BOTTOM_IS_ENTRY,
        nullable=False,
    )
    # Nombre minimal de frames pour valider une traversée complète (anti faux positifs).
    min_crossing_frames: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    # Fenêtre anti-doublon : délai minimal (secondes) entre deux événements d'un même track.
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # --- Seuils (spécifiques à cette caméra) ---
    # Part minimale de la séance pour être PRÉSENT / EN RETARD.
    present_threshold: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    late_threshold: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    # Seuil de similarité cosinus pour identifier un étudiant.
    face_match_threshold: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
