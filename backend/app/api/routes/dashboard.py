"""
Route du tableau de bord administrateur.

Fournit en un seul appel les chiffres clés de la page d'accueil : effectif,
présents / absents du jour et derniers événements. Protégée par
l'authentification administrateur.
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.crud import dashboard as crud_dashboard
from app.schemas.dashboard import DashboardSummary, RecentEvent

router = APIRouter(
    prefix="/dashboard",
    tags=["Tableau de bord"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    on_date: date | None = Query(
        None, alias="date", description="Jour de reference (defaut : aujourd'hui)"
    ),
    limit: int = Query(10, ge=1, le=50, description="Nombre d'evenements recents"),
    db: Session = Depends(get_db),
):
    """
    Renvoie les indicateurs du tableau de bord pour une date (aujourd'hui par défaut).

    Le nombre de présents s'appuie sur les résultats déjà calculés : il faut donc
    avoir déclenché le calcul (`POST /attendance/compute`) pour que ce chiffre
    reflète la journée.
    """
    reference_date = on_date or date.today()

    total_students = crud_dashboard.count_students(db)
    present_today = crud_dashboard.count_present_students(db, reference_date)
    absent_today = max(0, total_students - present_today)

    events = crud_dashboard.recent_events(db, limit=limit)
    recent = [
        RecentEvent(
            id=event.id,
            student_id=event.student_id,
            student_name=full_name,
            event_type=event.event_type,
            timestamp=event.timestamp,
        )
        for event, full_name in events
    ]

    return DashboardSummary(
        date=reference_date,
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today,
        recent_events=recent,
    )
