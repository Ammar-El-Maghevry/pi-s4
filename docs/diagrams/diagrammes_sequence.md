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

## 3. Calcul de présence — *implémenté*

Source : `app/api/routes/attendance.py`, `app/services/attendance/*`,
`app/crud/attendance_event.py`, `app/crud/attendance_result.py`,
`app/crud/schedule.py`.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as API FastAPI<br/>(routes/attendance.py)
    participant Svc as Service présence<br/>(services/attendance/service.py)
    participant Engine as Moteur pur<br/>(intervals.py + engine.py)
    participant CRUD as Couche CRUD<br/>(events / results / schedule)
    participant DB as Base PostgreSQL

    Client->>API: POST /api/v1/attendance/compute?date=YYYY-MM-DD<br/>(&student_id optionnel)
    Note over API: route protégée par get_current_user

    alt student_id fourni mais introuvable
        API-->>Client: 404 « Etudiant introuvable »
    else calcul lancé
        API->>Svc: compute_date(db, on_date, student_id)

        alt student_id absent
            Svc->>CRUD: distinct_student_ids_with_events_on_date(db, on_date)
            CRUD->>DB: SELECT DISTINCT student_id des événements du jour
            DB-->>CRUD: liste d'étudiants
            CRUD-->>Svc: [étudiants avec événements]
        end

        loop pour chaque étudiant
            Svc->>CRUD: get_events_for_student_on_date(db, student_id, on_date)
            CRUD->>DB: SELECT événements (triés par timestamp)
            DB-->>Svc: entrées / sorties brutes
            Svc->>Engine: build_intervals(events)
            Engine-->>Svc: intervalles [entrée→sortie] (sortie manquante = ouvert)

            loop pour chaque séance (SessionType.SESSION)
                Svc->>Engine: compute_session(intervals, window_start, window_end)
                Note over Engine: taux de chevauchement → present / late / absent
                Engine-->>Svc: SessionComputation { status, entry_time, exit_time }
                Svc->>CRUD: upsert_result(...) (idempotent)
                CRUD->>DB: INSERT/UPDATE attendance_results<br/>(contrainte uq_presence_unique)
            end
        end

        Svc->>DB: COMMIT
        Svc-->>API: ComputeReport { students_processed, sessions_per_student, results_written }
        API-->>Client: 200 ComputeReportRead
    end
```

---

## 4. Flux caméra (une caméra + ligne de franchissement) — *(cible / phase future — NON IMPLÉMENTÉ)*

> ⚠️ **Ce flux n'existe pas encore dans le code.** Le service IA est un simple
> **producteur d'événements** : il écrit les mêmes `attendance_events` que la
> saisie manuelle (`POST /api/v1/events`), puis le calcul de présence (section 3,
> déjà implémenté) s'applique sans changement. Diagramme reconstitué à partir de
> `app/services/ai/README.md` et de
> `docs/detection_entree_sortie_camera_unique.md`.

```mermaid
sequenceDiagram
    autonumber
    participant Cam as Caméra unique<br/>(entrée de la salle)
    participant Pipe as Pipeline vision<br/>RetinaFace + ByteTrack<br/>+ MiniFASNet + InsightFace<br/>(à définir)
    participant Line as Ligne de franchissement<br/>(LineCrossingDirection — à définir)
    participant API as API événements<br/>(POST /api/v1/events)
    participant Engine as Calcul de présence<br/>(section 3 — implémenté)
    participant DB as Base PostgreSQL

    Cam->>Pipe: flux vidéo (une seule caméra)

    Note over Pipe: Détection (RetinaFace) → suivi (ByteTrack)<br/>→ anti-spoofing (MiniFASNet) → reconnaissance
    Pipe->>DB: recherche d'identité par similarité cosinus<br/>(pgvector, seuil FACE_MATCH_THRESHOLD) sur face_embedding
    DB-->>Pipe: étudiant reconnu (ou inconnu)

    Pipe->>Line: track { id, trajectoire, identité, horodatage }
    Note over Line: sens de traversée de la ligne virtuelle<br/>validé sur N frames + cooldown anti-doublon
    alt Traversée haut → bas
        Line->>Line: sens = ENTRÉE (entry)
    else Traversée bas → haut
        Line->>Line: sens = SORTIE (exit)
    else Pas de traversée complète
        Line->>Line: ignoré (arrêt sur le seuil / bruit)
    end

    Line->>API: POST /events { student_id, event_type, camera_id } (+ Snapshot)
    API->>DB: INSERT INTO attendance_events (...)
    DB-->>API: événement enregistré

    Note over Engine,DB: Périodiquement / en fin de séance (cf. section 3)
    Engine->>DB: POST /attendance/compute → calcul du statut
    DB-->>Engine: attendance_results (present / late / absent)
```
