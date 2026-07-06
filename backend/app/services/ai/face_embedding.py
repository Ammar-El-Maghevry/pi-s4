"""
Extraction d'embedding facial (InsightFace, CPU).

Utilisé à la fois par l'enrôlement (une photo -> un embedding stocké) et, plus
tard, par la reconnaissance en direct (une frame -> comparaison aux embeddings
enrôlés). Les deux doivent utiliser le même modèle pour rester comparables.

Le modèle est chargé paresseusement (au premier appel) et mis en cache : le
téléchargement des poids (~326 Mo, une seule fois) et le chargement ONNX sont
coûteux et inutiles si l'API ne sert jamais de requête de reconnaissance.
"""
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from app.config import settings


class NoFaceDetected(Exception):
    """Aucun visage détecté dans l'image fournie."""


class MultipleFacesDetected(Exception):
    """Plusieurs visages détectés : l'enrôlement exige une photo avec un seul visage."""


@dataclass
class DetectedFace:
    embedding: list[float]
    bbox: tuple[float, float, float, float]
    det_score: float


@lru_cache
def _get_model():
    """Charge (une seule fois) le modèle InsightFace buffalo_l en CPU."""
    from insightface.app import FaceAnalysis  # noqa: PLC0415

    model = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    model.prepare(ctx_id=-1, det_size=(640, 640))
    return model


def decode_image(image_bytes: bytes):
    """Décode des octets JPEG/PNG en image OpenCV (BGR)."""
    import cv2  # noqa: PLC0415

    array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Image illisible (format non supporte ou fichier corrompu).")
    return frame


def extract_single_face_embedding(image_bytes: bytes) -> DetectedFace:
    """
    Extrait l'embedding du visage unique présent dans l'image.

    Lève `NoFaceDetected` / `MultipleFacesDetected` si l'image ne contient pas
    exactement un visage : l'enrôlement doit être sans ambiguïté.
    """
    frame = decode_image(image_bytes)
    faces = _get_model().get(frame)

    if len(faces) == 0:
        raise NoFaceDetected("Aucun visage detecte dans la photo.")
    if len(faces) > 1:
        raise MultipleFacesDetected(
            f"{len(faces)} visages detectes : la photo doit contenir une seule personne."
        )

    face = faces[0]
    return DetectedFace(
        embedding=face.normed_embedding.astype(float).tolist(),
        bbox=tuple(float(v) for v in face.bbox),
        det_score=float(face.det_score),
    )


def extract_all_face_embeddings(frame) -> list[DetectedFace]:
    """Extrait tous les visages d'une frame (utilisé par la reconnaissance en direct)."""
    faces = _get_model().get(frame)
    return [
        DetectedFace(
            embedding=f.normed_embedding.astype(float).tolist(),
            bbox=tuple(float(v) for v in f.bbox),
            det_score=float(f.det_score),
        )
        for f in faces
    ]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Similarite cosinus entre deux embeddings normalises (deja normed_embedding)."""
    va, vb = np.asarray(a), np.asarray(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def match_student(
    embedding: list[float],
    candidates: list[tuple[int, list[float]]],
    threshold: float | None = None,
) -> tuple[int, float] | None:
    """
    Compare un embedding aux étudiants enrôlés, retourne (student_id, score) du
    meilleur candidat si son score dépasse le seuil, sinon None.
    """
    match_threshold = settings.FACE_MATCH_THRESHOLD if threshold is None else threshold
    best_id: int | None = None
    best_score = -1.0
    for student_id, candidate_embedding in candidates:
        score = cosine_similarity(embedding, candidate_embedding)
        if score > best_score:
            best_id, best_score = student_id, score
    if best_id is not None and best_score >= match_threshold:
        return best_id, best_score
    return None
