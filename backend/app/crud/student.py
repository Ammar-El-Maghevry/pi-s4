"""
Couche d'accès aux données pour les étudiants.

Fournit les opérations de création, lecture, mise à jour, suppression et
recherche.
"""
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate


def get_student(db: Session, student_pk: int) -> Student | None:
    """Récupère un étudiant par sa clé primaire."""
    return db.query(Student).filter(Student.id == student_pk).first()


def get_student_by_matricule(db: Session, student_id: str) -> Student | None:
    """Récupère un étudiant par son numéro d'étudiant (matricule)."""
    return db.query(Student).filter(Student.student_id == student_id).first()


def list_students(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> list[Student]:
    """
    Liste les étudiants avec pagination et recherche optionnelle.

    La recherche porte sur le nom, le matricule et le département
    (insensible à la casse).
    """
    query = db.query(Student)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Student.full_name.ilike(pattern),
                Student.student_id.ilike(pattern),
                Student.department.ilike(pattern),
            )
        )
    return query.order_by(Student.full_name).offset(skip).limit(limit).all()


def create_student(db: Session, data: StudentCreate) -> Student:
    """Crée un nouvel étudiant (sans embedding facial à ce stade)."""
    student = Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def update_student(db: Session, student: Student, data: StudentUpdate) -> Student:
    """Met à jour un étudiant avec uniquement les champs fournis."""
    # `exclude_unset=True` : on ignore les champs non transmis dans la requête.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


def delete_student(db: Session, student: Student) -> None:
    """Supprime un étudiant."""
    db.delete(student)
    db.commit()
