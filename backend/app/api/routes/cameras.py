"""
Routes de configuration des caméras (CRUD + test de connexion).

L'administrateur configure ici la connexion et les paramètres de détection de
chaque caméra, sans toucher au code ni au .env. Toutes les routes sont protégées
par l'authentification administrateur (`get_current_user`).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user, get_db
from app.crud import camera as crud_camera
from app.models.enums import CameraSourceType
from app.schemas.camera import (
    CameraCreate,
    CameraRead,
    CameraTestResult,
    CameraUpdate,
    EmailSendResult,
)
from app.services.camera import (
    close_phone_camera_session,
    get_phone_camera_status,
    test_camera_connection,
)
from app.services.email import send_pairing_email

router = APIRouter(
    prefix="/cameras",
    tags=["Cameras"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[CameraRead])
def list_cameras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Liste les caméras configurées (source_url masquée)."""
    return crud_camera.list_cameras(db, skip=skip, limit=limit)


@router.post("", response_model=CameraRead, status_code=status.HTTP_201_CREATED)
def create_camera(data: CameraCreate, db: Session = Depends(get_db)):
    """Ajoute une nouvelle caméra."""
    return crud_camera.create_camera(db, data)


@router.get("/{camera_pk}", response_model=CameraRead)
def get_camera(camera_pk: int, db: Session = Depends(get_db)):
    """Récupère une caméra par son identifiant."""
    camera = crud_camera.get_camera(db, camera_pk)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera introuvable")
    return camera


@router.put("/{camera_pk}", response_model=CameraRead)
async def update_camera(camera_pk: int, data: CameraUpdate, db: Session = Depends(get_db)):
    """
    Modifie la configuration d'une caméra.

    Route async (le reste du CRUD caméra est synchrone) uniquement pour
    pouvoir fermer, sur la vraie boucle d'évènements du serveur, la session
    WebRTC d'un éventuel ancien jeton téléphone — cette fermeture réseau ne
    peut pas se faire en sécurité depuis un thread de pool synchrone.
    """
    camera = crud_camera.get_camera(db, camera_pk)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera introuvable")
    try:
        updated, stale_token = crud_camera.update_camera(db, camera, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if stale_token:
        await close_phone_camera_session(stale_token)
    return updated


@router.delete("/{camera_pk}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_pk: int, db: Session = Depends(get_db)):
    """Supprime une caméra (voir `update_camera` pour la raison d'être async)."""
    camera = crud_camera.get_camera(db, camera_pk)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera introuvable")
    stale_token = crud_camera.delete_camera(db, camera)
    if stale_token:
        await close_phone_camera_session(stale_token)


@router.post("/{camera_pk}/test-connection", response_model=CameraTestResult)
def test_connection(camera_pk: int, db: Session = Depends(get_db)):
    """
    Teste la connexion à la caméra : ouvre le flux et lit une image.

    Utilise la valeur complète de `source_url` (identifiants inclus) côté serveur,
    sans jamais la renvoyer au client. Ne bloque pas durablement.
    """
    camera = crud_camera.get_camera(db, camera_pk)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera introuvable")

    if camera.source_type == CameraSourceType.PHONE:
        result = get_phone_camera_status(camera.webrtc_token)
    else:
        result = test_camera_connection(camera.source_url)
    return CameraTestResult(
        success=result.success,
        message=result.message,
        width=result.width,
        height=result.height,
    )


@router.post("/{camera_pk}/send-pairing-email", response_model=EmailSendResult)
def send_camera_pairing_email(camera_pk: int, db: Session = Depends(get_db)):
    """Envoie (ou renvoie) le lien d'appairage d'une caméra téléphone par e-mail."""
    camera = crud_camera.get_camera(db, camera_pk)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera introuvable")
    if camera.source_type != CameraSourceType.PHONE or not camera.webrtc_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette camera n'est pas une camera telephone appairee",
        )
    if not camera.pairing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun email configure pour cette camera",
        )

    link = f"{settings.PHONE_PAIRING_BASE_URL}/phone-camera/{camera.webrtc_token}"
    try:
        send_pairing_email(camera.pairing_email, camera.name, link)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Envoi de l'email echoue : {exc}"
        ) from exc
    return EmailSendResult(success=True, message=f"Email envoye a {camera.pairing_email}")
