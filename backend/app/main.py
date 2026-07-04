"""
Point d'entrée de l'application FastAPI.

Lancement en développement :
    uvicorn app.main:app --reload

La documentation interactive est disponible sur /docs (Swagger).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="API de gestion de presence par reconnaissance faciale (phase 1).",
)

# CORS : autorise le frontend React (Vite) à appeler l'API pendant le développement.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Systeme"])
def health_check():
    """Vérifie que l'API est en ligne."""
    return {"status": "ok"}
