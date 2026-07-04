# Détection des entrées et sorties à l'aide de deux caméras

## Décision architecturale

Le système retient une configuration à **deux caméras** pour déterminer le sens de déplacement de l'étudiant (entrée ou sortie), plutôt qu'une seule caméra reposant sur une « ligne de franchissement virtuelle ».

En effet, la caméra unique déduit le sens à partir du vecteur de déplacement de la personne à travers une ligne tracée dans l'image. Cette méthode est sensible aux erreurs : elle échoue lorsque l'étudiant s'arrête sur le seuil, en cas d'affluence, ou lorsqu'une partie du corps est masquée. La configuration à deux caméras, elle, détermine le sens à partir de **l'ordre chronologique d'apparition** de l'étudiant dans deux zones distinctes, ce qui est nettement plus fiable.

---

## Principe de fonctionnement

Deux caméras sont installées à l'entrée de la salle :

- **Caméra extérieure (A)** : couvre le côté extérieur de la porte (le couloir).
- **Caméra intérieure (B)** : couvre le côté intérieur de la porte (dans la salle).

Le sens se déduit de la séquence d'observation d'un même étudiant dans les deux caméras :

| Séquence chronologique d'observation | Sens déduit |
|--------------------------------------|-------------|
| Apparition dans A puis dans B | **Entrée** (entry) |
| Apparition dans B puis dans A | **Sortie** (exit) |
| Apparition dans une seule caméra | Événement incertain (ignoré ou signalé pour révision) |

Les deux apparitions doivent se produire dans une **fenêtre temporelle courte** (quelques secondes, par exemple) pour être considérées comme un seul franchissement, et non comme deux observations indépendantes.

---

## Point critique : la corrélation entre les deux caméras

L'algorithme de suivi ByteTrack fonctionne **uniquement au sein d'un seul flux caméra** ; l'identifiant de suivi (track ID) attribué par la caméra A n'a aucune signification dans la caméra B. On ne peut donc pas s'appuyer sur le numéro de suivi pour relier les deux observations.

La solution : la corrélation se fait via l'**empreinte faciale (face embedding)**. L'identité de l'étudiant est reconnue séparément dans chaque caméra grâce à InsightFace, puis on compare l'**identité** (et non le numéro de suivi) pour apparier les deux observations. La séquence réelle est donc :

> L'étudiant *X* est observé dans la caméra A à l'instant t1, puis le même étudiant *X* est observé dans la caméra B à l'instant t2 (avec t2 > t1, dans la fenêtre temporelle) ⟶ un unique événement **entrée** est enregistré.

---

## Modifications du pipeline de traitement

Le pipeline traite désormais **deux flux en parallèle** au lieu d'un seul, avec une nouvelle couche de corrélation :

```
Caméra A ─┐                                     ┌─ Caméra B
          ↓                                     ↓
  Détection du visage (RetinaFace)     Détection du visage (RetinaFace)
          ↓                                     ↓
     Suivi (ByteTrack)                     Suivi (ByteTrack)
          ↓                                     ↓
 Anti-spoofing + reconnaissance     Anti-spoofing + reconnaissance
          ↓                                     ↓
 Observation (identité + heure + caméra)  Observation (identité + heure + caméra)
          └──────────────────┬──────────────────┘
                             ↓
            Module de corrélation (Correlator)
   apparie les identités entre les deux caméras
              dans une fenêtre temporelle
                             ↓
      Émission d'un seul événement entrée/sortie + capture
```

Le **module de corrélation (Correlator)** est le nouveau composant : il conserve temporairement les dernières observations de chaque caméra, apparie les identités, et émet un événement unique portant le bon sens de déplacement.

---

## Impact sur la base de données

- Le champ `camera_id` de la table `attendance_events` (déjà ajouté) prend désormais **un sens réel** : il indique quelle caméra a détecté l'étudiant.
- Il est recommandé d'ajouter un paramètre de **rôle de la caméra** (`camera_role` : `exterior` / `interior`) dans le fichier de configuration, afin que le module de corrélation sache quelle caméra est extérieure et quelle caméra est intérieure.
- L'événement stocké reste unique (une entrée ou une sortie), et non deux observations ; la corrélation a lieu dans le service d'inférence, avant l'enregistrement.

---

## Avantages et coûts

**Avantages :**
- Détermination du sens plus fiable, résistante à l'arrêt de l'étudiant sur le seuil et à l'affluence.
- Redondance : si une caméra rate une prise, l'autre peut compenser.
- Meilleure précision dans la distinction entrée/sortie par rapport à la ligne de franchissement virtuelle.

**Coûts :**
- **Doublement de la charge d'inférence** : deux flux impliquent deux fois plus d'opérations de détection et de reconnaissance, ce qui renforce le besoin d'un processeur graphique (GPU). Ce point est directement lié à la décision matérielle encore en suspens.
- Complexité supplémentaire liée à la synchronisation temporelle entre les deux caméras et à la logique de corrélation.
- Coût d'installation et de câblage d'une seconde caméra.

---

## Cas limites à traiter

- Apparition de l'étudiant dans une seule caméra (occultation ou passage rapide) : classé comme événement incertain.
- Passage de plusieurs étudiants simultanément : le module de corrélation doit apparier chaque identité séparément.
- Étudiant immobile dans l'encadrement de la porte pendant une période prolongée : la fenêtre d'apaisement (cooldown) l'empêche de générer des événements en double.
- Conflit de séquence (apparition quasi simultanée dans les deux caméras) : résolu par une comparaison précise des horodatages, ou signalé pour révision manuelle.
