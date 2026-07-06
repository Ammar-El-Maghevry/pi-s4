"""
Routeur principal de l'API v1.

Regroupe tous les sous-routeurs. Les modules des phases suivantes
(présence, rapports, caméra, reconnaissance) seront ajoutés ici.
"""
from fastapi import APIRouter

from app.api.routes import (
    attendance,
    auth,
    cameras,
    dashboard,
    events,
    phone_camera,
    reports,
    schedules,
    students,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(schedules.router)
api_router.include_router(events.router)
api_router.include_router(attendance.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
api_router.include_router(cameras.router)
api_router.include_router(phone_camera.router)

# Phases suivantes (à activer plus tard) :
# api_router.include_router(camera.router)  # service caméra/inférence temps réel
