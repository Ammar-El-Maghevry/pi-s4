# Service IA — reconnaissance faciale et pipeline caméra (phase future)

> **Statut : non implémenté.** Ce module décrit l'interface **prévue** du service
> temps réel. Aucun code d'inférence n'est présent dans le backend actuel : la
> reconnaissance faciale, la détection, le suivi et la corrélation deux caméras
> feront l'objet d'un module séparé (voir `../../../detection_entree_sortie_deux_cameras.md`).

Le backend actuel est volontairement **testable sans caméra ni GPU** : les
événements de présence (`attendance_events`) peuvent être injectés manuellement
via `POST /api/v1/events`, puis le moteur de calcul (`services/attendance/`)
produit les résultats. Le service IA décrit ici ne fait que **remplacer la
saisie manuelle par une détection automatique** — il écrit les mêmes événements.

## Place dans l'architecture

```
Camera A ─┐                                   ┌─ Camera B
          ↓                                   ↓
   Detecteur (RetinaFace)             Detecteur (RetinaFace)
          ↓                                   ↓
    Suivi (ByteTrack)                   Suivi (ByteTrack)
          ↓                                   ↓
 Anti-spoofing + Reconnaissance   Anti-spoofing + Reconnaissance
   (MiniFASNet + InsightFace)       (MiniFASNet + InsightFace)
          └────────────────┬────────────────┘
                           ↓
                  Correlateur (identite)
                           ↓
        POST /api/v1/events  (entree / sortie + camera_id)
```

Le service IA est un **producteur d'événements** : il s'appuie sur l'API HTTP
existante (ou, plus tard, sur la couche CRUD directement) et n'introduit aucune
dépendance inverse. Le backend reste ignorant de la manière dont les événements
sont produits.

## Interfaces prévues (à implémenter plus tard)

```python
class FaceDetector(Protocol):
    """Detection de visages dans une image (ex. RetinaFace)."""
    def detect(self, frame) -> list[FaceBox]: ...

class FaceRecognizer(Protocol):
    """Extraction d'embedding et identification (ex. InsightFace / ArcFace, 512-d)."""
    def embed(self, face_image) -> list[float]: ...
    def identify(self, embedding) -> StudentMatch | None: ...  # recherche pgvector + seuil

class SpoofDetector(Protocol):
    """Anti-spoofing : rejette photos et ecrans (ex. MiniFASNet)."""
    def is_live(self, face_image) -> bool: ...

class Tracker(Protocol):
    """Suivi intra-camera (ex. ByteTrack). Le track_id n'a de sens que dans un flux."""
    def update(self, detections) -> list[Track]: ...

class Correlator(Protocol):
    """
    Apparie les identites entre les deux cameras dans une fenetre temporelle
    pour deduire le sens (entree/sortie), puis emet UN evenement unique.
    La correlation se fait sur l'IDENTITE (embedding), pas sur le track_id.
    """
    def observe(self, camera_role: str, student_id: int, at: datetime) -> AttendanceEvent | None: ...
```

## Points d'intégration déjà en place

- Colonne `students.face_embedding` (`Vector(512)`, pgvector) prête pour l'enrôlement.
- `settings.FACE_EMBEDDING_DIM` (512) et `settings.FACE_MATCH_THRESHOLD` (0.5).
- Champ `attendance_events.camera_id` (rôle `exterior` / `interior` à configurer).
- Table `snapshots` pour la capture liée à chaque événement.

## Dépendances à ajouter le moment venu

Non incluses dans `requirements.txt` (lourdes, GPU) : `insightface`,
`onnxruntime` (ou `onnxruntime-gpu`), `opencv-python`, `numpy`, et
l'implémentation ByteTrack / MiniFASNet retenue.
