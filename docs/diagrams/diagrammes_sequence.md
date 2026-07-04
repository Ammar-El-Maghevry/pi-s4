# Diagrammes de séquence (UML)

Participants réels du code : **Client**, **API FastAPI**, **Dépendances/JWT**
(`core/deps.py` + `core/security.py`), **Couche CRUD** (`crud/*`),
**Base PostgreSQL**.

---

## 1. Authentification (connexion administrateur) — *implémenté*

Source : `app/api/routes/auth.py`, `app/crud/user.py`, `app/core/security.py`.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as API FastAPI<br/>(routes/auth.py)
    participant JWT as Dépendances / JWT<br/>(core/security.py)
    participant CRUD as Couche CRUD<br/>(crud/user.py)
    participant DB as Base PostgreSQL

    Client->>API: POST /api/v1/auth/login<br/>(username=email, password)
    API->>CRUD: authenticate_user(db, email, password)
    CRUD->>DB: SELECT * FROM users WHERE email = :email
    DB-->>CRUD: utilisateur (ou aucun)
    CRUD->>JWT: verify_password(password, hashed_password)
    JWT-->>CRUD: vrai / faux (bcrypt)

    alt Identifiants invalides
        CRUD-->>API: None
        API-->>Client: 401 « Email ou mot de passe incorrect »
    else Identifiants valides
        CRUD-->>API: utilisateur
        API->>JWT: create_access_token(subject=user.email)
        JWT-->>API: jeton JWT (HS256, sub=email, exp)
        API-->>Client: 200 Token { access_token, token_type="bearer" }
    end
```

---

## 2. Création d'un étudiant (requête protégée) — *implémenté*

Source : `app/api/routes/students.py`, `app/core/deps.py`, `app/crud/student.py`.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as API FastAPI<br/>(routes/students.py)
    participant JWT as Dépendances / JWT<br/>(core/deps.py)
    participant CRUD as Couche CRUD<br/>(crud/student.py)
    participant DB as Base PostgreSQL

    Client->>API: POST /api/v1/students<br/>Authorization: Bearer <jeton><br/>{ full_name, student_id, ... }

    Note over API,JWT: Dépendance get_current_user (protège la route)
    API->>JWT: get_current_user(token)
    JWT->>JWT: decode_access_token(token) -> email
    alt Jeton invalide / expiré
        JWT-->>API: 401
        API-->>Client: 401 « Identifiants invalides ou jeton expiré »
    else Jeton valide
        JWT->>DB: SELECT * FROM users WHERE email = :email
        DB-->>JWT: administrateur (is_active ?)
        JWT-->>API: administrateur courant
    end

    Note over API,DB: Vérification d'unicité du matricule
    API->>CRUD: get_student_by_matricule(db, student_id)
    CRUD->>DB: SELECT * FROM students WHERE student_id = :student_id
    DB-->>CRUD: étudiant existant (ou aucun)
    CRUD-->>API: résultat

    alt Matricule déjà présent
        API-->>Client: 409 « Un étudiant avec ce matricule existe déjà »
    else Matricule libre
        API->>CRUD: create_student(db, data)
        CRUD->>DB: INSERT INTO students (...) + COMMIT
        DB-->>CRUD: étudiant créé
        CRUD-->>API: étudiant
        API-->>Client: 201 StudentRead (has_face_embedding dérivé)
    end
```

---

## 3. Reconnaissance et calcul de présence — *(cible / phase future — NON IMPLÉMENTÉ)*

> ⚠️ **Ce flux n'existe pas encore dans le code.** Aucun module `services/`,
> aucune route caméra/présence, aucune écriture dans `attendance_events` /
> `attendance_results`. Diagramme reconstitué à partir de la feuille de route
> (`backend/README.md`) et de la note d'architecture
> (`detection_entree_sortie_deux_cameras.md`). Les composants marqués
> *à définir* restent à concevoir.

```mermaid
sequenceDiagram
    autonumber
    participant CamA as Caméra A (extérieure)
    participant CamB as Caméra B (intérieure)
    participant Pipe as Pipeline vision<br/>RetinaFace + ByteTrack + InsightFace<br/>(à définir)
    participant Corr as Module de corrélation<br/>(Correlator — à définir)
    participant CRUD as Couche CRUD événements<br/>(à définir)
    participant Engine as Moteur de calcul<br/>de présence (phase 6 — à définir)
    participant DB as Base PostgreSQL

    CamA->>Pipe: flux vidéo (couloir)
    CamB->>Pipe: flux vidéo (salle)

    Note over Pipe: Détection visage -> suivi -> anti-spoofing -> reconnaissance
    Pipe->>DB: recherche d'identité par similarité cosinus<br/>(pgvector, seuil 0.5) sur face_embedding
    DB-->>Pipe: étudiant reconnu (ou inconnu)
    Pipe->>Corr: Observation { identité, caméra, horodatage }

    Note over Corr: Appariement des identités entre A et B<br/>dans une fenêtre temporelle courte
    alt Séquence A puis B
        Corr->>Corr: sens = ENTRÉE (entry)
    else Séquence B puis A
        Corr->>Corr: sens = SORTIE (exit)
    else Une seule caméra
        Corr->>Corr: événement incertain (ignoré / à réviser)
    end

    Corr->>CRUD: enregistrer AttendanceEvent + Snapshot
    CRUD->>DB: INSERT INTO snapshots (...)
    CRUD->>DB: INSERT INTO attendance_events<br/>(student_id, event_type, timestamp, confidence, camera_id, snapshot_id)
    DB-->>CRUD: événement enregistré

    Note over Engine,DB: Périodiquement / en fin de séance
    Engine->>DB: SELECT événements par étudiant et séance
    DB-->>Engine: entrées / sorties brutes
    Engine->>Engine: corréler entrée/sortie -> statut<br/>(present / late / absent)
    Engine->>DB: UPSERT attendance_results<br/>(contrainte uq_presence_unique)
    DB-->>Engine: présence calculée
```
