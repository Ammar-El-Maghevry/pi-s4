"""
Couche d'accès aux données pour les enseignants et leur présence.

Miroir de `crud/student.py`, en plus simple (pas de matricule, pas de
département/classe) et avec la présence en plus (`teacher_attendance`).
"""
from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.teacher import Teacher
from app.models.teacher_attendance import TeacherAttendance
from app.schemas.teacher import TeacherCreate, TeacherUpdate


def get_teacher(db: Session, teacher_pk: int) -> Teacher | None:
    """Récupère un enseignant par sa clé primaire."""
    return db.query(Teacher).filter(Teacher.id == teacher_pk).first()


def list_teachers(db: Session, skip: int = 0, limit: int = 100, search: str | None = None) -> list[Teacher]:
    """Liste les enseignants avec pagination et recherche optionnelle (nom, email)."""
    query = db.query(Teacher)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Teacher.full_name.ilike(pattern), Teacher.email.ilike(pattern)))
    return query.order_by(Teacher.full_name).offset(skip).limit(limit).all()


def create_teacher(db: Session, data: TeacherCreate) -> Teacher:
    """Crée un nouvel enseignant (sans embedding facial à ce stade)."""
    teacher = Teacher(**data.model_dump())
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def update_teacher(db: Session, teacher: Teacher, data: TeacherUpdate) -> Teacher:
    """Met à jour un enseignant avec uniquement les champs fournis."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(teacher, field, value)
    db.commit()
    db.refresh(teacher)
    return teacher


def delete_teacher(db: Session, teacher: Teacher) -> None:
    """Supprime un enseignant."""
    db.delete(teacher)
    db.commit()


def set_teacher_photo(db: Session, teacher: Teacher, photo_path: str, face_embedding: list[float]) -> Teacher:
    """Enregistre le chemin de la photo et l'embedding facial calcule."""
    teacher.photo_path = photo_path
    teacher.face_embedding = face_embedding
    db.commit()
    db.refresh(teacher)
    return teacher


def list_face_candidates(db: Session) -> list[tuple[int, list[float]]]:
    """Retourne (id, embedding) pour les enseignants enroles (utilise par la reconnaissance en direct)."""
    rows = db.query(Teacher.id, Teacher.face_embedding).filter(Teacher.face_embedding.isnot(None)).all()
    return [(teacher_id, list(embedding)) for teacher_id, embedding in rows]


def get_attendance_for_date(db: Session, on_date: date) -> dict[int, bool]:
    """Retourne {teacher_id: present} pour tous les enseignants ayant un statut ce jour-là."""
    rows = (
        db.query(TeacherAttendance.teacher_id, TeacherAttendance.is_present)
        .filter(TeacherAttendance.attendance_date == on_date)
        .all()
    )
    return {teacher_id: is_present for teacher_id, is_present in rows}


def set_attendance(
    db: Session, teacher_id: int, on_date: date, is_present: bool, source: str
) -> TeacherAttendance:
    """Positionne (upsert) la présence d'un enseignant pour une date donnée."""
    record = (
        db.query(TeacherAttendance)
        .filter(TeacherAttendance.teacher_id == teacher_id, TeacherAttendance.attendance_date == on_date)
        .first()
    )
    if record is None:
        record = TeacherAttendance(teacher_id=teacher_id, attendance_date=on_date)
        db.add(record)
    record.is_present = is_present
    record.source = source
    db.commit()
    db.refresh(record)
    return record
