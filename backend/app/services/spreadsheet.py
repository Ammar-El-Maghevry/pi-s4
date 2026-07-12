"""
Lecture generique de feuilles de calcul (CSV ou XLSX) en liste de
dictionnaires, avec normalisation des en-tetes via une table d'alias fournie
par l'appelant.

Partagee par les differents imports en masse (etudiants, emploi du temps) :
seule la table d'alias et le traitement metier des lignes changent d'un
import a l'autre.
"""
import csv
import io

import openpyxl


class SpreadsheetFormatError(Exception):
    """Format de fichier non supporte (ni .csv ni .xlsx)."""


def _normalize_header(raw: str, aliases: dict[str, str]) -> str | None:
    return aliases.get(raw.strip().lower())


def read_csv_rows(content: bytes, aliases: dict[str, str]) -> list[dict[str, str]]:
    """Parse un CSV en dicts {colonne_normalisee: valeur}. Ignore les lignes vides."""
    text = content.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return []
    headers = [_normalize_header(h, aliases) for h in rows[0]]
    result = []
    for raw_row in rows[1:]:
        if not any(cell.strip() for cell in raw_row):
            continue
        record: dict[str, str] = {}
        for header, value in zip(headers, raw_row):
            if header:
                record[header] = value.strip()
        result.append(record)
    return result


def read_xlsx_rows(content: bytes, aliases: dict[str, str]) -> list[dict[str, str]]:
    """Parse la premiere feuille d'un classeur Excel en dicts {colonne_normalisee: valeur}."""
    workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
    sheet = workbook.active
    rows_iter = sheet.iter_rows(values_only=True)
    try:
        header_row = next(rows_iter)
    except StopIteration:
        return []
    headers = [_normalize_header(str(h), aliases) if h is not None else None for h in header_row]
    result = []
    for raw_row in rows_iter:
        if raw_row is None or not any(cell not in (None, "") for cell in raw_row):
            continue
        record: dict[str, str] = {}
        for header, value in zip(headers, raw_row):
            if header:
                record[header] = "" if value is None else str(value).strip()
        result.append(record)
    return result


def read_rows(content: bytes, filename: str, aliases: dict[str, str]) -> list[dict[str, str]]:
    """Choisit le parseur CSV ou XLSX selon l'extension du fichier."""
    lower = filename.lower()
    if lower.endswith(".csv"):
        return read_csv_rows(content, aliases)
    if lower.endswith(".xlsx"):
        return read_xlsx_rows(content, aliases)
    raise SpreadsheetFormatError("Format non supporte : utilisez un fichier .csv ou .xlsx")
