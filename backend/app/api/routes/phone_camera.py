"""
Routes publiques pour l'appairage d'une caméra téléphone.

Contrairement à `cameras.py`, ce routeur n'a AUCUNE dépendance d'authentification
admin : la page /phone-camera/<token> tourne dans le navigateur du téléphone,
qui n'a pas de session administrateur. La sécurité repose sur le `webrtc_token`
(secret aléatoire, non devinable) transmis dans le lien d'appairage.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import camera as crud_camera
from app.models.enums import CameraSourceType
from app.schemas.camera import PhoneCameraInfo, WebRTCAnswer, WebRTCOffer
from app.services.camera import close_phone_camera_session, handle_phone_camera_offer

router = APIRouter(prefix="/phone-camera", tags=["Camera telephone"])


def _get_phone_camera_or_404(db: Session, token: str):
    camera = crud_camera.get_camera_by_token(db, token)
    if camera is None or camera.source_type != CameraSourceType.PHONE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lien invalide")
    return camera


@router.get("/{token}", response_model=PhoneCameraInfo)
def get_phone_camera_info(token: str, db: Session = Depends(get_db)):
    """Informations minimales affichées sur la page d'appairage du téléphone."""
    return _get_phone_camera_or_404(db, token)


@router.post("/{token}/offer", response_model=WebRTCAnswer)
async def post_offer(token: str, offer: WebRTCOffer, db: Session = Depends(get_db)):
    """Reçoit l'offre SDP du téléphone et renvoie la réponse SDP du serveur."""
    camera = _get_phone_camera_or_404(db, token)
    if not camera.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera inactive")

    sdp, sdp_type = await handle_phone_camera_offer(token, offer.sdp, offer.type)
    return WebRTCAnswer(sdp=sdp, type=sdp_type)


@router.post("/{token}/stop", status_code=status.HTTP_204_NO_CONTENT)
async def post_stop(token: str, db: Session = Depends(get_db)):
    """Ferme la session WebRTC en cours (bouton « Arreter » côté téléphone)."""
    _get_phone_camera_or_404(db, token)
    await close_phone_camera_session(token)
