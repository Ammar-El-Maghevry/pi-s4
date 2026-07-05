"""
Test de connexion à une caméra.

Tente d'ouvrir le flux (OpenCV) et de lire UNE seule frame, avec un délai
d'attente court, pour vérifier que la caméra est joignable et renvoyer sa
résolution.

Contraintes respectées :
- OpenCV est importé **paresseusement** (au premier appel), jamais au démarrage
  de l'API : cela évite de charger une dépendance lourde inutilement.
- Si OpenCV n'est pas installé, on renvoie un message clair au lieu de planter.
- La fonction est défensive (try/except) et ne lève pas d'exception vers la route.
"""
from dataclasses import dataclass

from app.schemas.camera import mask_source_url


@dataclass
class ConnectionResult:
    """Résultat brut d'un test de connexion (mappé ensuite vers CameraTestResult)."""
    success: bool
    message: str
    width: int | None = None
    height: int | None = None


def _normalize_source(source_url: str):
    """
    Convertit la source en argument accepté par cv2.VideoCapture.

    Un index USB numérique ("0", "1"...) est converti en entier ; sinon on garde
    l'URL telle quelle (RTSP, fichier, etc.).
    """
    return int(source_url) if source_url.strip().isdigit() else source_url


def test_camera_connection(source_url: str, timeout_ms: int = 3000) -> ConnectionResult:
    """
    Ouvre le flux, lit une frame et renvoie le résultat.

    `timeout_ms` : délai d'ouverture / lecture souhaité (best-effort selon le
    backend OpenCV). La fonction reste courte et ne bloque pas durablement.
    """
    if not source_url:
        return ConnectionResult(False, "Aucune source configuree pour cette camera.")

    # Import paresseux : OpenCV n'est chargé qu'ici, pas au démarrage de l'API.
    try:
        import cv2  # noqa: PLC0415
    except ImportError:
        return ConnectionResult(
            False,
            "OpenCV (opencv-python-headless) n'est pas installe : test de connexion indisponible.",
        )

    source = _normalize_source(source_url)
    capture = None
    try:
        # Délai d'ouverture / lecture (best-effort, ignoré par certains backends).
        # IMPORTANT : ces propriétés doivent être passées AU constructeur — les
        # fixer après coup via `capture.set()` n'a aucun effet sur l'ouverture,
        # qui est bloquante et a déjà eu lieu dans `VideoCapture(...)`.
        open_params = []
        for prop in ("CAP_PROP_OPEN_TIMEOUT_MSEC", "CAP_PROP_READ_TIMEOUT_MSEC"):
            code = getattr(cv2, prop, None)
            if code is not None:
                open_params.extend([code, timeout_ms])
        capture = cv2.VideoCapture(source, cv2.CAP_ANY, open_params)

        if not capture.isOpened():
            return ConnectionResult(False, "Impossible d'ouvrir le flux (camera injoignable).")

        ok, frame = capture.read()
        if not ok or frame is None:
            return ConnectionResult(False, "Flux ouvert mais aucune image n'a pu etre lue.")

        height, width = frame.shape[:2]
        return ConnectionResult(
            True, "Connexion reussie : une image a ete lue.", width=int(width), height=int(height)
        )
    except Exception as exc:  # pragma: no cover - dépend du matériel/réseau
        # Les erreurs OpenCV/FFmpeg peuvent contenir l'URL complète (identifiants
        # inclus) : on masque le message avant de le renvoyer au client.
        return ConnectionResult(False, f"Erreur lors du test : {mask_source_url(str(exc))}")
    finally:
        if capture is not None:
            capture.release()
