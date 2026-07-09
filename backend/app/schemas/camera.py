"""
Schémas Pydantic pour les caméras.

Point de sécurité important : le `source_url` contient souvent des identifiants
(rtsp://user:motdepasse@host). Le schéma de lecture (`CameraRead`) **masque**
systématiquement cette partie ; la valeur complète n'existe qu'en base, pour un
usage interne par le futur service caméra.
"""
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.config import settings
from app.models.enums import CameraSourceType, CrossingDirection

# Motif : capture les identifiants entre "://" et "@" pour les remplacer.
_CREDENTIALS_RE = re.compile(r"(://)([^@/]+)@")

# Valeur de `source_url` stockée pour une caméra téléphone (jamais utilisée
# pour ouvrir un flux : le flux réel vit en mémoire, indexé par `webrtc_token`).
PHONE_SOURCE_URL_PLACEHOLDER = "phone-camera"


def mask_source_url(url: str) -> str:
    """
    Masque les identifiants d'une URL de flux.

    rtsp://admin:secret@192.168.1.10:554/stream → rtsp://***:***@192.168.1.10:554/stream
    Une source sans identifiants (index USB, URL publique) est renvoyée telle quelle.
    """
    if not url:
        return url
    return _CREDENTIALS_RE.sub(r"\1***:***@", url)


class CameraBase(BaseModel):
    """Champs communs de configuration d'une caméra."""
    name: str = Field(min_length=1, max_length=100)
    location: str | None = Field(default=None, max_length=150)
    source_type: CameraSourceType = CameraSourceType.IP_CAMERA
    # Obligatoire uniquement pour une caméra IP (voir `_check_source_url` ci-dessous) ;
    # ignoré/ecrase par le CRUD pour une caméra téléphone.
    source_url: str | None = Field(default=None, max_length=512)
    # Adresse a laquelle envoyer (sur demande) le lien d'appairage par e-mail.
    pairing_email: EmailStr | None = None
    is_active: bool = True

    line_x1: int | None = None
    line_y1: int | None = None
    line_x2: int | None = None
    line_y2: int | None = None
    crossing_direction: CrossingDirection = CrossingDirection.TOP_TO_BOTTOM_IS_ENTRY
    min_crossing_frames: int = Field(default=3, ge=1)
    cooldown_seconds: int = Field(default=5, ge=0)

    present_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    late_threshold: float = Field(default=0.2, ge=0.0, le=1.0)
    face_match_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check_thresholds(self):
        """Le seuil de présence doit être strictement supérieur au seuil de retard."""
        if self.present_threshold <= self.late_threshold:
            raise ValueError(
                "present_threshold doit etre strictement superieur a late_threshold"
            )
        return self

    @model_validator(mode="after")
    def _check_source_url(self):
        """Une caméra IP a besoin d'une source_url non vide ; une caméra téléphone non."""
        if self.source_type == CameraSourceType.IP_CAMERA and not (self.source_url or "").strip():
            raise ValueError("source_url est obligatoire pour une camera IP")
        return self


class CameraCreate(CameraBase):
    """Données requises pour créer une caméra (name et source_url obligatoires)."""
    pass


class CameraUpdate(BaseModel):
    """
    Données pour modifier une caméra : tous les champs sont optionnels.

    Les seuils fournis sont validés dans [0, 1] ; si les deux seuils sont
    fournis ensemble, on vérifie present > late.
    """
    name: str | None = Field(default=None, min_length=1, max_length=100)
    location: str | None = None
    source_type: CameraSourceType | None = None
    source_url: str | None = None
    pairing_email: EmailStr | None = None
    is_active: bool | None = None

    line_x1: int | None = None
    line_y1: int | None = None
    line_x2: int | None = None
    line_y2: int | None = None
    crossing_direction: CrossingDirection | None = None
    min_crossing_frames: int | None = Field(default=None, ge=1)
    cooldown_seconds: int | None = Field(default=None, ge=0)

    present_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    late_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    face_match_threshold: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check_thresholds(self):
        """Vérifie present > late uniquement si les deux seuils sont fournis."""
        if (
            self.present_threshold is not None
            and self.late_threshold is not None
            and self.present_threshold <= self.late_threshold
        ):
            raise ValueError(
                "present_threshold doit etre strictement superieur a late_threshold"
            )
        return self


class CameraRead(BaseModel):
    """Représentation renvoyée par l'API : `source_url` masquée."""
    id: int
    name: str
    location: str | None = None
    source_type: CameraSourceType
    source_url: str
    # Jeton d'appairage du lien /phone-camera/<token> (caméras téléphone uniquement) ;
    # non masqué, ce n'est pas un identifiant de connexion et seuls les admins le voient.
    webrtc_token: str | None = None
    pairing_email: str | None = None
    # Calcule depuis PHONE_PAIRING_BASE_URL (backend) plutot que window.location
    # cote frontend : l'admin peut consulter le tableau de bord via "localhost",
    # ce qui produirait un lien inutilisable pour le telephone.
    pairing_link: str | None = None
    is_active: bool

    line_x1: int | None = None
    line_y1: int | None = None
    line_x2: int | None = None
    line_y2: int | None = None
    crossing_direction: CrossingDirection
    min_crossing_frames: int
    cooldown_seconds: int

    present_threshold: float
    late_threshold: float
    face_match_threshold: float

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("source_url", mode="before")
    @classmethod
    def _mask(cls, value):
        """Masque les identifiants avant de renvoyer l'URL."""
        return mask_source_url(value) if isinstance(value, str) else value


class CameraTestResult(BaseModel):
    """Résultat d'un test de connexion à une caméra."""
    success: bool
    message: str
    width: int | None = None
    height: int | None = None


class PhoneCameraInfo(BaseModel):
    """
    Informations publiques renvoyées à la page /phone-camera/<token>.

    Volontairement minimal : la page tourne dans le navigateur du téléphone,
    sans authentification admin, donc aucun réglage sensible (seuils, ligne de
    franchissement) n'est exposé ici.
    """
    name: str
    location: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class WebRTCOffer(BaseModel):
    """Offre SDP envoyée par le téléphone pour démarrer la diffusion."""
    sdp: str
    type: str


class WebRTCAnswer(BaseModel):
    """Réponse SDP renvoyée par le serveur."""
    sdp: str
    type: str


class EmailSendResult(BaseModel):
    """Résultat de l'envoi du lien d'appairage par e-mail."""
    success: bool
    message: str
