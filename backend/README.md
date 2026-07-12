# Backend — Système de présence intelligent (Phase 1)

Squelette du backend : **FastAPI + SQLAlchemy + Alembic**, authentification
**JWT** et gestion complète des étudiants (**CRUD + recherche**). Architecture
en couches (modèles / schémas / CRUD / routes), prête à accueillir les modules
des phases suivantes (reconnaissance faciale, caméra, calcul de présence,
rapports).

## Ce qui fonctionne dans cette phase

- Connexion administrateur et jeton JWT (`/api/v1/auth/login`)
- CRUD étudiants + recherche par nom / matricule / département
- Six tables créées : `users`, `students`, `schedules`, `attendance_events`,
  `attendance_results`, `snapshots`
- Colonne `face_embedding` (pgvector, 512 dim.) déjà prévue mais non utilisée
- Emploi du temps des 5 séances inséré automatiquement

## Prérequis

- Python 3.11+
- Docker (pour PostgreSQL avec pgvector)

## Installation~

```bash
# 1) Environnement virtuel
python -m venv .venv
source .venv/bin/activate          # sous fish : source .venv/bin/activate.fish

# 2) Dépendances
pip install -r requirements.txt

# 3) Variables d'environnement
cp .env.example .env

# 4) Base de données (PostgreSQL + pgvector)
docker compose up -d
```

## Migrations et données initiales

```bash
# Génère la première migration à partir des modèles
alembic revision --autogenerate -m "init schema"

# Applique les migrations
alembic upgrade head

# Crée l'admin par défaut et l'emploi du temps
python -m app.initial_data
```

## Lancer l'API

```bash
uvicorn app.main:app --reload
```

- Documentation interactive (Swagger) : http://localhost:8000/docs
- Test de santé : http://localhost:8000/health

## Compte administrateur par défaut

| Email             | Mot de passe |
|-------------------|--------------|
| admin@univ.local  | admin123     |

> À changer immédiatement. Pour tester dans Swagger : bouton **Authorize**,
> saisir l'email dans le champ `username` et le mot de passe.

## Diagrammes UML

Diagrammes fidèles au code de la phase 1 (les versions détaillées sont dans
`../docs/diagrams/`).

### Diagramme de classes

```mermaid
classDiagram
    direction LR

    class EventType {
        <<enumeration>>
        ENTRY
        EXIT
    }
    class SessionType {
        <<enumeration>>
        SESSION
        BREAK
    }
    class AttendanceStatus {
        <<enumeration>>
        PRESENT
        LATE
        ABSENT
    }

    class User {
        <<table users>>
        +int id
        +str email
        +str full_name
        +str hashed_password
        +bool is_active
        +datetime created_at
    }
    class Student {
        <<table students>>
        +int id
        +str full_name
        +str student_id
        +Optional~str~ email
        +Optional~str~ department
        +Optional~str~ photo_path
        +Optional~Vector512~ face_embedding
        +datetime created_at
        +datetime updated_at
    }
    class Schedule {
        <<table schedules>>
        +int id
        +int session_number
        +str name
        +Time start_time
        +Time end_time
        +SessionType session_type
    }
    class AttendanceEvent {
        <<table attendance_events>>
        +int id
        +int student_id
        +EventType event_type
        +datetime timestamp
        +Optional~float~ confidence
        +Optional~str~ camera_id
        +Optional~int~ snapshot_id
    }
    class AttendanceResult {
        <<table attendance_results>>
        +int id
        +int student_id
        +int schedule_id
        +date result_date
        +AttendanceStatus status
        +Optional~datetime~ entry_time
        +Optional~datetime~ exit_time
        +datetime computed_at
    }
    class Snapshot {
        <<table snapshots>>
        +int id
        +Optional~int~ student_id
        +str image_path
        +EventType event_type
        +datetime captured_at
    }

    Student "1" -- "*" AttendanceEvent : génère
    Student "1" -- "*" AttendanceResult : concerne
    Schedule "1" -- "*" AttendanceResult : évalue
    Student "1" -- "*" Snapshot : capture
    AttendanceEvent "*" -- "0..1" Snapshot : associé à

    Schedule ..> SessionType : utilise
    AttendanceEvent ..> EventType : utilise
    AttendanceResult ..> AttendanceStatus : utilise
    Snapshot ..> EventType : utilise
```

### Diagramme de séquence — Authentification (connexion administrateur)

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as API FastAPI
    participant JWT as Dépendances / JWT
    participant CRUD as Couche CRUD
    participant DB as Base PostgreSQL

    Client->>API: POST /api/v1/auth/login (username=email, password)
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

### Diagramme de séquence — Création d'un étudiant (route protégée)

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as API FastAPI
    participant JWT as Dépendances / JWT
    participant CRUD as Couche CRUD
    participant DB as Base PostgreSQL

    Client->>API: POST /api/v1/students (Bearer jeton, données étudiant)
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
        API-->>Client: 201 StudentRead
    end
```

## Structure du projet

```
app/
  config.py            Configuration (env, JWT, pgvector)
  database.py          Moteur et session SQLAlchemy
  main.py              Point d'entrée FastAPI
  initial_data.py      Admin par défaut + emploi du temps
  core/
    security.py        Hachage bcrypt + jetons JWT
    deps.py            Dépendances (session, utilisateur courant)
  models/              Tables ORM (6 modèles + énumérations)
  schemas/             Schémas Pydantic (validation API)
  crud/                Accès aux données (users, students)
  api/routes/          Routes (auth, students)
  services/            (vide) — logique métier des phases suivantes
alembic/               Migrations
docker-compose.yml     PostgreSQL + pgvector
```

## Prochaines étapes (feuille de route)

- **Phase 2** : enrôlement facial hors-ligne (InsightFace → embedding → pgvector)
- **Phase 3** : pipeline caméra (RetinaFace + ByteTrack + InsightFace)
- **Phase 4** : logique entrée/sortie (ligne de franchissement) + événements
- **Phase 5** : anti-spoofing (MiniFASNet)
- **Phase 6** : moteur de calcul de présence par séance
- **Phase 7** : frontend React
- **Phase 8** : rapports (PDF / Excel / CSV)
