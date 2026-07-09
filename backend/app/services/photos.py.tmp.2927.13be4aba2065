"""
Stockage des photos de reference sur disque.

Le nom de fichier est derive uniquement de l'identifiant interne (jamais du nom
fourni par le client) : aucune donnee utilisateur n'entre dans le chemin, ce qui
elimine tout risque de traversee de repertoire (path traversal).
"""
from pathlib import Path

from app.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_PHOTO_BYTES = 8 * 1024 * 1024  # 8 Mo


def _storage_root() -> Path:
    root = Path(settings.PHOTO_STORAGE_DIR)
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_student_photo(student_pk: int, content: bytes, content_type: str) -> str:
    """
    Enregistre la photo d'un etudiant, remplace toute photo precedente, et
    retourne le chemin relatif stocke en base (`students.photo_path`).
    """
    extension = ALLOWED_CONTENT_TYPES.get(content_type)
    if extension is None:
        raise ValueError(f"Type d'image non supporte : {content_type}")

    students_dir = _storage_root() / "students"
    students_dir.mkdir(parents=True, exist_ok=True)

    # Supprime toute photo precedente (extension eventuellement differente).
    for existing in students_dir.glob(f"{student_pk}.*"):
        existing.unlink(missing_ok=True)

    relative_path = f"students/{student_pk}{extension}"
    (students_dir / f"{student_pk}{extension}").write_bytes(content)
    return relative_path


def save_teacher_photo(teacher_pk: int, content: bytes, content_type: str) -> str:
    """
    Enregistre la photo d'un enseignant, remplace toute photo precedente, et
    retourne le chemin relatif stocke en base (`teachers.photo_path`).
    """
    extension = ALLOWED_CONTENT_TYPES.get(content_type)
    if extension is None:
        raise ValueError(f"Type d'image non supporte : {content_type}")

    teachers_dir = _storage_root() / "teachers"
    teachers_dir.mkdir(parents=True, exist_ok=True)

    for existing in teachers_dir.glob(f"{teacher_pk}.*"):
        existing.unlink(missing_ok=True)

    relative_path = f"teachers/{teacher_pk}{extension}"
    (teachers_dir / f"{teacher_pk}{extension}").write_bytes(content)
    return relative_path


def resolve_photo_path(relative_path: str) -> Path | None:
    """
    Resout un chemin relatif stocke en base vers un chemin absolu, en verifiant
    qu'il reste bien a l'interieur du repertoire de stockage.
    """
    root = _storage_root().resolve()
    candidate = (root / relative_path).resolve()
    if root not in candidate.parents and candidate != root:
        return None
    return candidate if candidate.is_file() else None
