"""
Schémas Pydantic pour les caméras.

Point de sécurité important : le `source_url` contient souvent des identifiants
(rtsp://user:motdepasse@host). Le schéma de lecture (`CameraRead`) **masque**
systématiquement cette partie ; la valeur complète n'existe qu'en base, pour un
usage interne par le futur service caméra.
"""
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import CrossingDirection

# Motif : capture les identifiants entre "://" et le DERNIER "@" du même mot.
# `\S+` gourmand couvre les mots de passe contenant "/" ou "@" ; en contrepartie,
# une URL sans identifiants dont le chemin contient "@" serait sur-masquée, ce
# qui est le sens d'erreur sûr (on ne fuit jamais un identifiant).
_CREDENTIALS_RE = re.compile(r"(://)(\S+)@")


def mask_source_url(url: str) -> str:
    """
    Masque les identifiants d'une URL de flux (ou dans un texte la contenant).

    rtsp://admin:secret@192.168.1.10:554/stream → rtsp://***:***@192.168.1.10:554/stream
    Une source sans identifiants (index USB, URL publique) est renvoyée telle quelle.
    """
    if not url:
        return url
    return _CREDENTIALS_RE.sub(r"\1***:***@", url)


class CameraBase(BaseModel):
    """Champs communs de configuration d'une caméra."""
    name: str
    location: str | None = None
    source_url: str
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


class CameraCreate(CameraBase):
    """Données requises pour créer une caméra (name et source_url obligatoires)."""
    pass


class CameraUpdate(BaseModel):
    """
    Données pour modifier une caméra : tous les champs sont optionnels.

    Les seuils fournis sont validés dans [0, 1] ; si les deux seuils sont
    fournis ensemble, on vérifie present > late.
    """
    name: str | None = None
    location: str | None = None
    source_url: str | None = None
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

    @model_validator(mode="after")
    def _reject_explicit_nulls(self):
        """
        Refuse un `null` explicite sur les champs NOT NULL en base.

        Seul `location` (et les coordonnées de ligne) peuvent être remis à null ;
        pour les autres champs, « optionnel » signifie « omis », pas « null » :
        laisser passer un null provoquerait une violation NOT NULL (erreur 500).
        """
        nullable_fields = {"location", "line_x1", "line_y1", "line_x2", "line_y2"}
        for field in self.model_fields_set:
            if field not in nullable_fields and getattr(self, field) is None:
                raise ValueError(f"Le champ '{field}' ne peut pas etre null")
        return self


class CameraRead(BaseModel):
    """Représentation renvoyée par l'API : `source_url` masquée."""
    id: int
    name: str
    location: str | None = None
    source_url: str
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
