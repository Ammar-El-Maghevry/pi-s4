"""Types énumérés utilisés par les modèles de la base de données."""
import enum


class EventType(str, enum.Enum):
    """Type d'un événement capté par la caméra."""
    ENTRY = "entry"  # entrée dans la salle
    EXIT = "exit"    # sortie de la salle


class SessionType(str, enum.Enum):
    """Nature d'un créneau de l'emploi du temps."""
    SESSION = "session"  # séance de cours
    BREAK = "break"      # pause


class AttendanceStatus(str, enum.Enum):
    """Statut de présence calculé pour un étudiant sur une séance."""
    PRESENT = "present"  # présent
    LATE = "late"        # en retard (présence partielle)
    ABSENT = "absent"    # absent


class CrossingDirection(str, enum.Enum):
    """
    Convention de sens pour la ligne de franchissement d'une caméra.

    Indique quelle traversée de la ligne virtuelle correspond à une entrée ;
    l'autre sens est alors une sortie.
    """
    TOP_TO_BOTTOM_IS_ENTRY = "top_to_bottom_is_entry"  # haut → bas = entrée
    BOTTOM_TO_TOP_IS_ENTRY = "bottom_to_top_is_entry"  # bas → haut = entrée


class CameraSourceType(str, enum.Enum):
    """Origine du flux vidéo d'une caméra."""
    IP_CAMERA = "ip_camera"  # flux RTSP/HTTP ou index USB, ouvert via OpenCV
    PHONE = "phone"          # navigateur d'un telephone, diffuse en direct via WebRTC
