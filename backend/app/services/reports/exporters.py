"""
Exports des rapports de présence : CSV, Excel (openpyxl) et PDF (reportlab).

Chaque fonction renvoie le contenu binaire du fichier (`bytes`), prêt à être
retourné par une réponse HTTP. Les bibliothèques openpyxl et reportlab sont
importées **paresseusement** (au premier usage) : l'application démarre même si
elles ne sont pas installées, et n'échoue que si l'on demande réellement ce
format.
"""
import csv
import io

from app.services.reports.aggregation import Report

# En-têtes communs à tous les formats tabulaires.
HEADERS = ["Matricule", "Etudiant", "Present", "Retard", "Absent", "Total", "Taux (%)"]


def _row_values(row) -> list:
    """Convertit une ligne de rapport en valeurs ordonnées selon HEADERS."""
    return [
        row.matricule,
        row.student_name,
        row.present,
        row.late,
        row.absent,
        row.total,
        row.attendance_rate,
    ]


def to_csv(report: Report) -> bytes:
    """Sérialise le rapport en CSV (encodage UTF-8 avec BOM pour Excel)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(HEADERS)
    for row in report.rows:
        writer.writerow(_row_values(row))
    # BOM pour qu'Excel ouvre correctement les accents.
    return buffer.getvalue().encode("utf-8-sig")


def to_excel(report: Report) -> bytes:
    """Sérialise le rapport en classeur Excel (.xlsx) via openpyxl."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Presence"

    # Ligne de titre.
    sheet.append([report.title])
    sheet.append([f"Periode : {report.start_date} -> {report.end_date}"])
    sheet.append([])  # ligne vide

    # En-têtes en gras.
    sheet.append(HEADERS)
    for cell in sheet[sheet.max_row]:
        cell.font = Font(bold=True)

    for row in report.rows:
        sheet.append(_row_values(row))

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def to_pdf(report: Report) -> bytes:
    """Sérialise le rapport en PDF via reportlab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=report.title)
    styles = getSampleStyleSheet()

    story = [
        Paragraph(report.title, styles["Title"]),
        Paragraph(
            f"Periode : {report.start_date} &rarr; {report.end_date}", styles["Normal"]
        ),
        Spacer(1, 16),
    ]

    data = [HEADERS] + [[str(v) for v in _row_values(row)] for row in report.rows]
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (2, 1), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(table)

    if not report.rows:
        story.append(Paragraph("Aucune donnee de presence sur la periode.", styles["Italic"]))

    doc.build(story)
    return buffer.getvalue()
