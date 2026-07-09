"""
Point d'entrée de l'application FastAPI.

Lancement en développement :
    uvicorn app.main:app --reload

La documentation interactive est disponible sur /docs (Swagger).
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings

logger = logging.getLogger("app")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="API de gestion de presence par reconnaissance faciale (phase 1).",
)

# CORS : autorise le frontend a appeler l'API. Origines configurables via
# CORS_ORIGINS (.env) pour s'adapter au deploiement (docker, autre port...).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def warn_if_insecure_secret_key() -> None:
    if settings.SECRET_KEY == "changez-cette-cle-en-production":
        logger.warning(
            "SECRET_KEY uses the insecure default value. Set a real SECRET_KEY "
            "in the environment before exposing this API beyond local dev."
        )


@app.on_event("startup")
def start_phone_camera_reaper() -> None:
    """Démarre le nettoyage périodique des sessions téléphone abandonnées."""
    from app.services.camera import start_phone_camera_reaper as _start

    _start()


@app.on_event("startup")
def warm_up_face_model() -> None:
    """
    Charge le modèle InsightFace dans un thread d'arrière-plan.

    Le premier chargement télécharge ~326 Mo de poids : sans ce warm-up, ce
    téléchargement se déclenchait lors du premier upload de photo, bloquant
    tout le processus (un seul worker uvicorn) pendant plusieurs minutes.
    """
    import threading

    from app.services.ai.face_embedding import _get_model

    threading.Thread(target=_get_model, daemon=True).start()


@app.on_event("startup")
def start_live_recognition() -> None:
    """Démarre la boucle de reconnaissance en direct (caméras téléphone / séance en cours)."""
    from app.services.attendance.live_recognition import start as _start

    _start()


@app.on_event("shutdown")
async def close_phone_camera_sessions() -> None:
    """Ferme proprement les sessions WebRTC de téléphone actives à l'arrêt."""
    from app.services.attendance.live_recognition import stop as stop_live_recognition
    from app.services.camera import shutdown_phone_camera_sessions, stop_phone_camera_reaper

    await stop_live_recognition()
    await stop_phone_camera_reaper()
    await shutdown_phone_camera_sessions()


@app.get("/health", tags=["Systeme"])
def health_check():
    """Vérifie que l'API est en ligne."""
    return {"status": "ok"}
