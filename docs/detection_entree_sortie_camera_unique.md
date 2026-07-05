# Détection des entrées et sorties avec une caméra unique (ligne de franchissement)

## Décision architecturale

Le système retient désormais une configuration à **une seule caméra**. Le sens de
déplacement de l'étudiant (entrée ou sortie) est déterminé par une **ligne de
franchissement virtuelle** tracée dans l'image : la personne est suivie image par
image, et l'on observe le sens dans lequel la trajectoire de son *track* traverse
cette ligne.

> Cette décision remplace l'ancienne configuration à deux caméras (corrélation
> par empreinte faciale), documentée dans
> `../detection_entree_sortie_deux_cameras.md`, désormais **obsolète**.

Motivations : coût matériel et de câblage réduit (une seule caméra), charge
d'inférence divisée par deux (un seul flux), et pipeline plus simple (pas de
module de corrélation ni de synchronisation entre deux flux).

---

## Principe de fonctionnement

Une caméra est installée à l'entrée de la salle. Sa connexion (URL RTSP ou index
USB) et sa ligne de franchissement sont **configurées par l'administrateur depuis
l'application** (API `/api/v1/cameras`, table `cameras`), sans toucher au code ni
au `.env`. Une ligne virtuelle est définie dans l'image (deux points). Le sens se
déduit de la traversée de cette ligne par le centre de la boîte suivie :

| Sens de traversée de la ligne | Sens déduit |
|-------------------------------|-------------|
| Haut → bas | **Entrée** (`entry`) |
| Bas → haut | **Sortie** (`exit`) |

Le suivi (ByteTrack) fournit un `track_id` stable au sein du flux, ce qui permet
de reconstituer la trajectoire d'une même personne d'une image à l'autre et donc
de savoir de quel côté de la ligne elle se trouvait avant / après.

Pipeline complet :

```
Camera (flux unique)
  → Detection du visage (RetinaFace)
  → Suivi (ByteTrack : track_id + trajectoire)
  → Anti-spoofing (MiniFASNet)
  → Reconnaissance (InsightFace / ArcFace : embedding 512-d, recherche pgvector)
  → Franchissement de ligne (sens de traversee → entree / sortie)
  → Emission d'un evenement entree/sortie + capture (Snapshot)
```

L'identité de l'étudiant est reconnue par l'embedding facial (recherche de
similarité cosinus dans pgvector, seuil `FACE_MATCH_THRESHOLD`). Le sens, lui,
ne dépend **pas** de la reconnaissance : il vient uniquement de la géométrie de la
traversée. Reconnaissance et sens sont donc deux informations indépendantes,
combinées au moment d'émettre l'événement.

---

## Limites et mitigations

| Limite | Risque | Mitigation |
|--------|--------|------------|
| **Arrêt sur le seuil** | La personne s'immobilise sur la ligne : oscillations, faux franchissements. | Ne valider une traversée que si le track franchit **complètement** la ligne sur un nombre minimal d'images consécutives (paramètre *frames min.*). |
| **Affluence / occultation** | Plusieurs personnes se croisent, un track est masqué puis réapparaît. | Placement de la caméra en **plongée** au-dessus de la porte (vue du dessus) pour limiter les occultations ; ByteTrack gère les ré-associations courtes. |
| **Passage rapide** | La personne traverse en très peu d'images. | Cadence caméra suffisante ; seuil *frames min.* adapté au débit réel. |
| **Doublons** | Une même personne génère plusieurs événements rapprochés (va-et-vient sur le seuil). | **Fenêtre de cooldown** (`COOLDOWN_SECONDS`) : délai minimal entre deux événements d'un même track. |

Cas résiduels (occultation totale prolongée, entrée/sortie hors champ) : classés
comme incertains et ignorés ou signalés — ils n'affectent pas la cohérence des
données déjà enregistrées.

---

## Impact sur la base de données et la logique métier

**La logique métier (moteur de présence, événements, dashboard, rapports) ne
change pas.** Le seul ajout au schéma est la table `cameras`, qui stocke la
configuration éditée par l'administrateur.

- Le champ `attendance_events.camera_id` **reste** : il identifie la caméra/salle
  (utile pour un futur multi-salles). En revanche, la notion de **rôle** de
  caméra (intérieur / extérieur) du schéma à deux caméras est **abandonnée**.
- La table `cameras` (voir `backend/app/models/camera.py`) porte, par caméra :
  `source_url` (masqué en lecture), `is_active`, la ligne de franchissement
  (`line_x1..line_y2`, `crossing_direction`), `min_crossing_frames`,
  `cooldown_seconds` et les seuils (`present_threshold`, `late_threshold`,
  `face_match_threshold`).
- Le service IA demeure un simple **producteur d'événements** entrée/sortie : il
  écrit les mêmes `attendance_events` que ceux saisis manuellement via
  `POST /api/v1/events`.
- Le moteur de présence (`app/services/attendance/`), les routes d'événements, le
  tableau de bord et les rapports sont **inchangés** : ils consomment les
  événements sans se soucier de leur origine (manuelle ou caméra).

Autrement dit, ce document ne concerne que la **façon de produire** les
événements ; toute la chaîne en aval reste identique et déjà testable sans
caméra.

---

## Paramètres de configuration (table `cameras`, éditée par l'admin)

Ces paramètres ne vivent plus dans `.env` : ils sont configurés via l'API
`/api/v1/cameras` et stockés par caméra dans la table `cameras`.

| Paramètre (colonne) | Rôle |
|---------------------|------|
| `source_url` | URL RTSP ou index USB de la caméra (masqué en lecture). |
| `is_active` | Caméra activée ou non. |
| `line_x1..line_y2` | Coordonnées des deux points de la ligne virtuelle. |
| `crossing_direction` | Convention de sens (haut→bas = entrée, ou l'inverse). |
| `min_crossing_frames` | Nb minimal de frames validant une traversée complète. |
| `cooldown_seconds` | Fenêtre anti-doublon entre deux événements d'un même track. |
| `present_threshold` / `late_threshold` | Seuils de présence / retard. |
| `face_match_threshold` | Seuil de similarité cosinus pour identifier un étudiant. |

> Le `.env` ne conserve que les secrets d'infrastructure (`SECRET_KEY`,
> `DATABASE_URL`). La dimension de l'embedding (`FACE_EMBEDDING_DIM = 512`,
> ArcFace) reste une constante applicative dans `app/config.py`.
