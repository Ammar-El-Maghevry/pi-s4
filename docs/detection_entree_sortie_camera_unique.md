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

Une caméra est installée à l'entrée de la salle. Une ligne virtuelle est
configurée dans l'image (deux points). Le sens se déduit de la traversée de cette
ligne par le centre de la boîte suivie :

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

**Aucun changement de schéma ni de logique métier.**

- Le champ `attendance_events.camera_id` **reste** : il identifie la caméra/salle
  (utile pour un futur multi-salles). En revanche, la notion de **rôle** de
  caméra (intérieur / extérieur) du schéma à deux caméras est **abandonnée**.
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

## Paramètres de configuration (`app/config.py`)

| Paramètre | Rôle |
|-----------|------|
| `CAMERA_ID` | Identifiant de la caméra/salle, stocké dans `attendance_events.camera_id`. |
| `LINE_CROSSING` | Coordonnées de la ligne virtuelle (2 points, placeholder). |
| `COOLDOWN_SECONDS` | Fenêtre anti-doublon entre deux événements d'un même track. |
| `FACE_MATCH_THRESHOLD` | Seuil de similarité cosinus pour identifier un étudiant. |
| `FACE_EMBEDDING_DIM` | Dimension de l'embedding (512, ArcFace). |
