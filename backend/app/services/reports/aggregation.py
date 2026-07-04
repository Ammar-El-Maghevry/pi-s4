"""
Agrégation des résultats de présence pour les rapports.

Transforme les lignes `attendance_results` en statistiques par étudiant sur une
période (journalière, hebdomadaire ou mensuelle) : nombre de séances présent /
retard / absent et taux de présence. Ces données alimentent ensuite les
exports (CSV, Excel, PDF).
"""
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum

from sqlalchemy.orm import Session

from app.models.attendance_result import AttendanceResult
from app.models.enums import AttendanceStatus
from app.models.student import Student


class ReportPeriod(str, Enum):
    """Granularité d'un rapport."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class StudentReportRow:
    """Statistiques de présence d'un étudiant sur la période."""
    student_id: int
    student_name: str
    matricule: str
    present: int = 0
    late: int = 0
    absent: int = 0

    @property
    def total(self) -> int:
        return self.present + self.late + self.absent

    @property
    def attendance_rate(self) -> float:
        """Taux de présence = (présent + retard) / total, en pourcentage."""
        if self.total == 0:
            return 0.0
        return round(100.0 * (self.present + self.late) / self.total, 1)


@dataclass
class Report:
    """Rapport agrégé complet, prêt à être exporté."""
    period: ReportPeriod
    start_date: date
    end_date: date
    rows: list[StudentReportRow] = field(default_factory=list)

    @property
    def title(self) -> str:
        labels = {
            ReportPeriod.DAILY: "journalier",
            ReportPeriod.WEEKLY: "hebdomadaire",
            ReportPeriod.MONTHLY: "mensuel",
        }
        return f"Rapport de presence {labels[self.period]}"


def period_range(period: ReportPeriod, reference: date) -> tuple[date, date]:
    """
    Calcule les bornes (incluses) de la période contenant la date de référence.

    - journalier  : la journée elle-même ;
    - hebdomadaire : du lundi au dimanche de la semaine ;
    - mensuel     : du 1er au dernier jour du mois.
    """
    if period == ReportPeriod.DAILY:
        return reference, reference
    if period == ReportPeriod.WEEKLY:
        start = reference - timedelta(days=reference.weekday())  # lundi
        return start, start + timedelta(days=6)
    # MONTHLY
    start = reference.replace(day=1)
    last_day = monthrange(reference.year, reference.month)[1]
    return start, reference.replace(day=last_day)


def build_report(db: Session, period: ReportPeriod, reference: date) -> Report:
    """
    Construit le rapport agrégé sur la période contenant `reference`.

    Parcourt les résultats calculés dans l'intervalle et cumule, par étudiant,
    le nombre de séances par statut.
    """
    start, end = period_range(period, reference)

    results = (
        db.query(AttendanceResult, Student.full_name, Student.student_id)
        .join(Student, AttendanceResult.student_id == Student.id)
        .filter(
            AttendanceResult.result_date >= start,
            AttendanceResult.result_date <= end,
        )
        .all()
    )

    rows: dict[int, StudentReportRow] = {}
    for result, full_name, matricule in results:
        row = rows.get(result.student_id)
        if row is None:
            row = StudentReportRow(
                student_id=result.student_id,
                student_name=full_name,
                matricule=matricule,
            )
            rows[result.student_id] = row

        if result.status == AttendanceStatus.PRESENT:
            row.present += 1
        elif result.status == AttendanceStatus.LATE:
            row.late += 1
        else:
            row.absent += 1

    ordered = sorted(rows.values(), key=lambda r: r.student_name)
    return Report(period=period, start_date=start, end_date=end, rows=ordered)
