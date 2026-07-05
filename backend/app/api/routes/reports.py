"""
Routes des rapports de présence.

Génère un rapport agrégé (journalier / hebdomadaire / mensuel) et le renvoie au
format demandé : CSV, Excel ou PDF. Protégée par l'authentification
administrateur.
"""
from datetime import date
from enum import Enum

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.services.reports import aggregation, exporters

router = APIRouter(
    prefix="/reports",
    tags=["Rapports"],
    dependencies=[Depends(get_current_user)],
)


class ReportFormat(str, Enum):
    """Format de sortie d'un rapport."""
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"


# Association format -> (fonction d'export, type MIME, extension de fichier).
_EXPORTERS = {
    ReportFormat.CSV: (exporters.to_csv, "text/csv", "csv"),
    ReportFormat.EXCEL: (
        exporters.to_excel,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xlsx",
    ),
    ReportFormat.PDF: (exporters.to_pdf, "application/pdf", "pdf"),
}


@router.get("")
def generate_report(
    period: aggregation.ReportPeriod = Query(
        aggregation.ReportPeriod.DAILY, description="Granularite du rapport"
    ),
    reference: date | None = Query(
        None, alias="date", description="Date de reference (defaut : aujourd'hui)"
    ),
    output: ReportFormat = Query(
        ReportFormat.CSV, alias="format", description="Format de sortie"
    ),
    db: Session = Depends(get_db),
):
    """
    Génère et télécharge un rapport de présence.

    - `period` : `daily`, `weekly` ou `monthly` (la période est calculée autour
      de la date de référence).
    - `format` : `csv`, `excel` ou `pdf`.
    """
    reference_date = reference or date.today()
    report = aggregation.build_report(db, period, reference_date)

    export_fn, media_type, extension = _EXPORTERS[output]
    content = export_fn(report)

    filename = f"presence_{period.value}_{report.start_date}_{report.end_date}.{extension}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
