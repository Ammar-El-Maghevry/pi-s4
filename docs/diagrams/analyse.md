# Analyse du backend — Système de présence intelligent (phase 1)

> Analyse fondée uniquement sur le code réel du dépôt (`backend/app/`), pas sur des suppositions.

## 1. Architecture en couches

Le backend applique une architecture en couches stricte : chaque couche ne connaît que la couche directement inférieure.

| Couche | Emplacement | Rôle réel observé dans le code |
|--------|-------------|--------------------------------|
| **Configuration** | `app/config.py` | Chargement des paramètres via `pydantic-settings` (URL base, `SECRET_KEY`, `ALGORITHM=HS256`, expiration jeton = 8 h, `FACE_EMBEDDING_DIM=512`, `FACE_MATCH_THRESHOLD=0.5`). Aucun secret codé en dur. |
| **Base de données** | `app/database.py` | `engine` PostgreSQL (`pool_pre_ping`), fabrique `SessionLocal`, classe `Base` (`DeclarativeBase`). |
| **Modèles ORM** | `app/models/*` | 6 tables SQLAlchemy 2.0 (`Mapped`/`mapped_column`) + 3 énumérations. |
| **Schémas Pydantic** | `app/schemas/*` | Validation entrée/sortie de l'API (séparés des modèles ORM). |
| **CRUD (accès données)** | `app/crud/*` | Isole les requêtes SQL des routes. Implémenté pour `user` et `student` uniquement. |
| **Sécurité / JWT** | `app/core/security.py`, `app/core/deps.py` | Hachage bcrypt (`passlib`), création/décodage JWT (`python-jose`), dépendances injectables `get_db` et `get_current_user`. |
| **Routes API** | `app/api/routes/*` + `app/api/router.py` | Expose `/auth` et `/students` sous le préfixe `/api/v1`. |
| **Point d'entrée** | `app/main.py` | Application FastAPI, middleware CORS (origine `http://localhost:5173`), route `/health`. |
| **Services (métier)** | `app/services/` | **Vide** — réservé aux phases futures. |
| **Migrations** | `alembic/env.py` | Autogenerate branché sur `Base.metadata` via l'import de `app.models`. |

## 2. Les six entités et leurs relations

- **`users`** : administrateurs (`id`, `email` unique, `full_name`, `hashed_password`, `is_active`, `created_at`). Seule table d'authentification ; sans relation FK.
- **`students`** : étudiants (`id`, `full_name`, `student_id` = matricule unique, `email?`, `department?`, `photo_path?`, `face_embedding?` de type `Vector(512)` pgvector nullable, `created_at`, `updated_at`).
- **`schedules`** : emploi du temps (`id`, `session_number`, `name`, `start_time`, `end_time`, `session_type` ∈ `SessionType`). Peuplé au démarrage (5 séances + pauses) par `initial_data.py`.
- **`attendance_events`** : événements bruts entrée/sortie (`event_type` ∈ `EventType`, `timestamp`, `confidence?`, `camera_id?`, `snapshot_id?`). FK `student_id` (CASCADE), FK `snapshot_id` (SET NULL).
- **`attendance_results`** : présence calculée par séance (`result_date`, `status` ∈ `AttendanceStatus`, `entry_time?`, `exit_time?`, `computed_at`). FK `student_id` + `schedule_id` (CASCADE), contrainte d'unicité `(student_id, schedule_id, result_date)`.
- **`snapshots`** : captures d'image (`image_path`, `event_type`, `captured_at`). FK `student_id` (SET NULL, nullable).

**Relations (déduites des `ForeignKey`) :**
- `Student` 1 — * `AttendanceEvent`
- `Student` 1 — * `AttendanceResult`
- `Schedule` 1 — * `AttendanceResult`
- `Student` 1 — * `Snapshot`
- `AttendanceEvent` * — 0..1 `Snapshot`

**Énumérations :** `EventType {entry, exit}`, `SessionType {session, break}`, `AttendanceStatus {present, late, absent}`.

## 3. Flux d'authentification (réel)

1. Le client appelle `POST /api/v1/auth/login` avec un `OAuth2PasswordRequestForm` (`username` = email, `password`).
2. `authenticate_user` (`crud/user.py`) récupère l'utilisateur par email puis vérifie le mot de passe avec `verify_password` (bcrypt).
3. En cas d'échec → `401`. En cas de succès → `create_access_token(subject=user.email)` génère un JWT `HS256` avec `sub` = email et `exp`.
4. La réponse est un schéma `Token { access_token, token_type="bearer" }`.
5. Pour les routes protégées, `get_current_user` (`core/deps.py`) décode le jeton, extrait le `sub`, recharge l'utilisateur et vérifie `is_active`. Toutes les routes `/students` sont protégées via `dependencies=[Depends(get_current_user)]`.

## 4. Ce qui est implémenté vs. prévu

**Implémenté (phase 1, vérifié dans le code) :**
- Authentification administrateur complète (login + `/auth/me`).
- CRUD étudiants complet + recherche paginée (`list/create/get/update/delete`), avec contrôle d'unicité du matricule (`409`) et champ dérivé `has_face_embedding`.
- Les 6 tables ORM et les 3 énumérations sont définies et migrables.
- Amorçage des données (`initial_data.py`) : admin par défaut + emploi du temps.
- Extension pgvector activée (`init-db/01-extensions.sql`) et colonne `face_embedding` déclarée.

**Prévu / non implémenté (structure présente, logique absente) :**
- **Reconnaissance faciale (phase 2)** : `face_embedding` reste `NULL` ; aucun code d'enrôlement InsightFace. → *à définir*
- **Pipeline caméra (phases 3-5)** : détection (RetinaFace), suivi (ByteTrack), anti-spoofing, corrélation deux caméras. Aucun module `services/` ni route caméra. → *à définir*
- **Écriture des événements** : la table `attendance_events` n'a **ni CRUD ni route** ; aucun code n'insère d'événement.
- **Calcul de présence (phase 6)** : la table `attendance_results` n'a **ni CRUD ni route** ; aucun moteur ne dérive `AttendanceStatus`.
- **Rapports (phase 8)** et **frontend React (phase 7)** : hors périmètre backend actuel.

Les sous-routeurs `attendance`, `reports`, `camera` sont explicitement commentés dans `app/api/router.py` comme « à activer plus tard ».
