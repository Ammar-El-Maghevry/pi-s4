"""
Paquet des rapports de présence.

- `aggregation` : agrégation des résultats par période (jour / semaine / mois).
- `exporters`   : sérialisation CSV, Excel (openpyxl) et PDF (reportlab).
"""
from app.services.reports.aggregation import (
    Report,
    ReportPeriod,
    StudentReportRow,
    build_report,
    period_range,
)
from app.services.reports.exporters import to_csv, to_excel, to_pdf

__all__ = [
    "Report",
    "ReportPeriod",
    "StudentReportRow",
    "build_report",
    "period_range",
    "to_csv",
    "to_excel",
    "to_pdf",
]
