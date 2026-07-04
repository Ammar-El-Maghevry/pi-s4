"""
Routeur principal de l'API v1.

Regroupe tous les sous-routeurs. Les modules des phases suivantes
(présence, rapports, caméra, reconnaissance) seront ajoutés ici.
"""
from fastapi import APIRouter

from app.api.routes import auth, students

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(students.router)

# Phases suivantes (à activer plus tard) :
# api_router.include_router(attendance.router)
# api_router.include_router(reports.router)
# api_router.include_router(camera.router)
