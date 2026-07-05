# Service IA — reconnaissance faciale et pipeline caméra (phase future)

> **Statut : non implémenté.** Ce module décrit l'interface **prévue** du service
> temps réel. Aucun code d'inférence n'est présent dans le backend actuel : la
> détection, le suivi, l'anti-spoofing, la reconnaissance et la détermination du
> sens de passage feront l'objet d'un module séparé
> (voir `../../../../docs/detection_entree_sortie_camera_unique.md`).

Le backend actuel est volontairement **testable sans caméra ni GPU** : les
événements de présence (`attendance_events`) peuvent être injectés manuellement
via `POST /api/v1/events`, puis le moteur de calcul (`services/attendance/`)
produit les résultats. Le service IA décrit ici ne fait que **remplacer la
saisie manuelle par une détection automatique** — il écrit les mêmes événements.

## Décision d'architecture : UNE seule caméra + ligne de franchissement

Le système utilise **une caméra unique** placée à l'entrée de la salle. Le sens
(entrée / sortie) est déterminé par une **ligne de franchissement virtuelle** :
la personne est suivie image par image (ByteTrack) et l'on observe le sens dans
lequel la trajectoire de son *track* traverse la ligne configurée.

- Traversée **haut → bas** de la ligne ⟶ **entrée** (`entry`)
- Traversée **bas → haut** de la ligne ⟶ **sortie** (`exit`)

Le sens positif et la position de la ligne sont **configurables** (voir plus bas).

## Place dans l'architecture

```
Camera (flux unique)
      ↓
 Detecteur (RetinaFace)              -> FaceDetector
      ↓
 Suivi (ByteTrack)                   -> Tracker (track_id + trajectoire)
      ↓
 Anti-spoofing (MiniFASNet)          -> SpoofDetector (rejette photo/ecran)
      ↓
 Reconnaissance (InsightFace/ArcFace)-> FaceRecognizer (embedding 512-d + pgvector)
      ↓
 Franchissement de ligne             -> LineCrossingDirection (sens du passage)
      ↓
 POST /api/v1/events  (entree / sortie + camera_id)  + Snapshot
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

class Tracker(Protocol):
    """
    Suivi intra-camera (ex. ByteTrack). Attribue un track_id stable et fournit
    la trajectoire (centre des boites successives) necessaire au franchissement.
    """
    def update(self, detections) -> list[Track]: ...

class SpoofDetector(Protocol):
    """Anti-spoofing : rejette photos et ecrans (ex. MiniFASNet)."""
    def is_live(self, face_image) -> bool: ...

class FaceRecognizer(Protocol):
    """Extraction d'embedding et identification (ex. InsightFace / ArcFace, 512-d)."""
    def embed(self, face_image) -> list[float]: ...
    def identify(self, embedding) -> StudentMatch | None: ...  # recherche pgvector + seuil

class LineCrossingDirection(Protocol):
    """
    Determine le sens de passage a partir de la trajectoire d'un track qui
    traverse une ligne virtuelle configurable.

    - haut -> bas  => ENTREE (entry)
    - bas  -> haut => SORTIE (exit)

    La traversee n'est validee que si le track franchit reellement la ligne sur
    un nombre minimal d'images (evite les faux positifs quand la personne
    s'arrete sur le seuil). Une fenetre de cooldown empeche les doublons pour un
    meme track.
    """
    def update(self, track_id: int, center_xy, at: datetime) -> AttendanceEvent | None: ...
```

## Paramètres de configuration attendus (caméra unique)

Déclarés (en placeholder) dans `app/config.py`, à préciser lors de l'implémentation :

| Paramètre | Rôle |
|-----------|------|
| `CAMERA_ID` | Identifiant de la caméra/salle, stocké dans `attendance_events.camera_id`. |
| `LINE_CROSSING` | Coordonnées de la ligne virtuelle (2 points, ex. `[[x1, y1], [x2, y2]]`). |
| *sens positif* | Convention de sens (haut→bas = entrée) ; à figer dans la config de la ligne. |
| *frames min.* | Nombre minimal d'images consécutives validant une traversée complète. |
| `COOLDOWN_SECONDS` | Fenêtre anti-doublon : délai minimal entre deux événements d'un même track. |

## Points d'intégration déjà en place

- Colonne `students.face_embedding` (`Vector(512)`, pgvector) prête pour l'enrôlement.
- `settings.FACE_EMBEDDING_DIM` (512) et `settings.FACE_MATCH_THRESHOLD` (0.5).
- Champ `attendance_events.camera_id` : conservé (utile pour un futur multi-salles) ;
  il n'y a **plus** de rôle intérieur/extérieur (abandon du schéma à deux caméras).
- Table `snapshots` pour la capture liée à chaque événement.

## Dépendances à ajouter le moment venu

Non incluses dans `requirements.txt` (lourdes, GPU) : `insightface`,
`onnxruntime` (ou `onnxruntime-gpu`), `opencv-python`, `numpy`, et
l'implémentation ByteTrack / MiniFASNet retenue.
