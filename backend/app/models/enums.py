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
