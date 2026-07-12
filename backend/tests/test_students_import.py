"""
Tests des helpers de parsing de l'import etudiants (couche pure, sans base
de donnees ni modele IA).

Couvre : reconnaissance des alias d'en-tetes, lignes vides ignorees, ainsi
que le traitement de l'archive ZIP (manifest + photos).
"""
import io
import zipfile

import openpyxl
import pytest

from app.services.students_import import (
    StudentImportError,
    _extract_zip,
    _rows_from_csv,
    _rows_from_xlsx,
)


# ------------------------------- CSV ------------------------------- #

def test_rows_from_csv_en_tetes_alias():
    content = "Nom,Matricule,E-mail,Departement\nAda Lovelace,S001,ada@example.com,CS\n".encode()
    rows = _rows_from_csv(content)
    assert rows == [
        {
            "full_name": "Ada Lovelace",
            "student_id": "S001",
            "email": "ada@example.com",
            "department": "CS",
        }
    ]


def test_rows_from_csv_ignore_lignes_vides():
    content = "full_name,student_id\nAda,S001\n,\n \n".encode()
    rows = _rows_from_csv(content)
    assert len(rows) == 1
    assert rows[0]["student_id"] == "S001"


def test_rows_from_csv_colonne_inconnue_ignoree():
    content = "full_name,student_id,extra\nAda,S001,whatever\n".encode()
    rows = _rows_from_csv(content)
    assert rows == [{"full_name": "Ada", "student_id": "S001"}]


def test_rows_from_csv_vide():
    assert _rows_from_csv(b"") == []


# ------------------------------- XLSX ------------------------------- #

def _make_xlsx(headers, data_rows) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in data_rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_rows_from_xlsx_en_tetes_alias():
    content = _make_xlsx(["name", "id", "email", "department"], [["Ada Lovelace", "S001", "ada@example.com", "CS"]])
    rows = _rows_from_xlsx(content)
    assert rows == [
        {
            "full_name": "Ada Lovelace",
            "student_id": "S001",
            "email": "ada@example.com",
            "department": "CS",
        }
    ]


def test_rows_from_xlsx_ignore_lignes_vides():
    content = _make_xlsx(["full_name", "student_id"], [["Ada", "S001"], [None, None]])
    rows = _rows_from_xlsx(content)
    assert len(rows) == 1


def test_rows_from_xlsx_sans_donnees():
    content = _make_xlsx(["full_name", "student_id"], [])
    assert _rows_from_xlsx(content) == []


# ------------------------------- ZIP ------------------------------- #

def _make_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_extract_zip_manifest_et_photos():
    manifest = "full_name,student_id\nAda,S001\n".encode()
    archive = _make_zip(
        {
            "students.csv": manifest,
            "photos/S001.jpg": b"fake-jpeg-bytes",
            "__MACOSX/._students.csv": b"junk",
        }
    )
    manifest_bytes, manifest_ext, photo_map = _extract_zip(archive)
    assert manifest_bytes == manifest
    assert manifest_ext == ".csv"
    assert set(photo_map) == {"S001"}
    assert photo_map["S001"] == (b"fake-jpeg-bytes", "image/jpeg")


def test_extract_zip_sans_manifest_leve_erreur():
    archive = _make_zip({"photos/S001.jpg": b"data"})
    with pytest.raises(StudentImportError):
        _extract_zip(archive)


def test_extract_zip_invalide_leve_erreur():
    with pytest.raises(StudentImportError):
        _extract_zip(b"not a zip file")
