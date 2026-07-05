"""
Routes de configuration des caméras (CRUD + test de connexion).

L'administrateur configure ici la connexion et les paramètres de détection de
chaque caméra, sans toucher au code ni au .env. Toutes les routes sont protégées
par l'authentification administrateur (`get_current_user`).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.crud import camera as crud_camera
from app.schemas.camera import (
    CameraCreate,
    CameraRead,
    CameraTestResult,
    CameraUpdate,
)
from app.services.camera import test_camera_connection

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
def update_camera(camera_pk: int, data: CameraUpdate, db: Session = Depends(get_db)):
    """Modifie la configuration d'une caméra."""
    camera = crud_camera.get_camera(db, camera_pk)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera introuvable")
    return crud_camera.update_camera(db, camera, data)


@router.delete("/{camera_pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(camera_pk: int, db: Session = Depends(get_db)):
    """Supprime une caméra."""
    camera = crud_camera.get_camera(db, camera_pk)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera introuvable")
    crud_camera.delete_camera(db, camera)


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

    result = test_camera_connection(camera.source_url)
    return CameraTestResult(
        success=result.success,
        message=result.message,
        width=result.width,
        height=result.height,
    )
