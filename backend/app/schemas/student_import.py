"""Schémas de réponse pour l'import en masse d'étudiants."""
from pydantic import BaseModel


class StudentImportRowError(BaseModel):
    row: int
    reason: str


class StudentImportMissingPhoto(BaseModel):
    id: int
    full_name: str
    student_id: str


class StudentImportResult(BaseModel):
    total_rows: int
    created: int
    duplicates: int
    invalid: int
    missing_photo: int
    photo_failed: int
    missing_photo_students: list[StudentImportMissingPhoto]
    errors: list[StudentImportRowError]
