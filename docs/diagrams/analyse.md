# Analyse du backend — Système de présence intelligent

> Analyse fondée sur le code réel du dépôt (`backend/app/`), pas sur des suppositions.

## 1. Architecture en couches

Le backend applique une architecture en couches stricte : chaque couche ne connaît que la couche directement inférieure.

| Couche | Emplacement | Rôle réel observé dans le code |
|--------|-------------|--------------------------------|
| **Configuration** | `app/config.py` | Chargement des paramètres via `pydantic-settings` (URL base, `SECRET_KEY`, `ALGORITHM=HS256`, expiration jeton = 8 h, `FACE_EMBEDDING_DIM=512`, `FACE_MATCH_THRESHOLD=0.5`, SMTP, `PHONE_PAIRING_BASE_URL`, seuils présence/retard globaux). |
| **Base de données** | `app/database.py` | `engine` PostgreSQL (`pool_pre_ping`), fabrique `SessionLocal`, classe `Base` (`DeclarativeBase`). |
| **Modèles ORM** | `app/models/*` | 7 tables SQLAlchemy 2.0 (`Mapped`/`mapped_column`) + 5 énumérations. |
| **Schémas Pydantic** | `app/schemas/*` | Validation entrée/sortie de l'API (séparés des modèles ORM). |
| **CRUD (accès données)** | `app/crud/*` | Isole les requêtes SQL des routes. Implémenté pour 8 modules. |
| **Sécurité / JWT** | `app/core/security.py`, `app/core/deps.py` | Hachage bcrypt (`passlib`), création/décodage JWT (`python-jose`), dépendances injectables `get_db` et `get_current_user`. |
| **Routes API** | `app/api/routes/*` + `app/api/router.py` | 10 routeurs sous le préfixe `/api/v1`. |
| **Point d'entrée** | `app/main.py` | Application FastAPI, middleware CORS, route `/health`, démarrage de la boucle de reconnaissance faciale en direct + du reaper de sessions WebRTC, arrêt des sessions au shutdown. |
| **Services (métier)** | `app/services/*` | 5 sous-systèmes : photos, email, IA (InsightFace), présence (intervalles + moteur + orchestration), rapports (agrégation + export), caméra (WebRTC + test connexion). |
| **Migrations** | `alembic/env.py` | Autogenerate branché sur `Base.metadata` via l'import de `app.models`. 5 migrations appliquées. |

## 2. Les sept entités et leurs relations

- **`users`** : administrateurs (`id`, `email` unique, `full_name`, `hashed_password`, `is_active`, `created_at`). Seule table d'authentification ; sans relation FK.
- **`students`** : étudiants (`id`, `full_name`, `student_id` = matricule unique, `email?`, `department?`, `photo_path?`, `face_embedding?` de type `Vector(512)` pgvector nullable, `created_at`, `updated_at`).
- **`schedules`** : emploi du temps (`id`, `session_number`, `name`, `start_time`, `end_time`, `session_type` ∈ `SessionType`, `camera_id?` FK → `cameras` SET NULL). Peuplé par `initial_data.py` (5 séances + 4 pauses) modifiable via l'API.
- **`cameras`** : caméras configurées (`id`, `name`, `location?`, `source_type` ∈ `CameraSourceType`, `source_url`, `webrtc_token?` unique, `pairing_email?`, `is_active`, ligne de franchissement, seuils, `created_at`, `updated_at`).
- **`attendance_events`** : événements bruts entrée/sortie (`event_type` ∈ `EventType`, `timestamp`, `confidence?`, `camera_id?`, `snapshot_id?`). FK `student_id` (CASCADE), FK `snapshot_id` (SET NULL).
- **`attendance_results`** : présence calculée par séance (`result_date`, `status` ∈ `AttendanceStatus`, `entry_time?`, `exit_time?`, `computed_at`). FK `student_id` + `schedule_id` (CASCADE), contrainte d'unicité `(student_id, schedule_id, result_date)`.
- **`snapshots`** : captures d'image (`image_path`, `event_type`, `captured_at`). FK `student_id` (SET NULL, nullable).

**Relations (déduites des `ForeignKey`) :**
- `Student` 1 — * `AttendanceEvent`
- `Student` 1 — * `AttendanceResult`
- `Schedule` 1 — * `AttendanceResult`
- `Schedule` * — 0..1 `Camera` (FK `camera_id`)
- `Camera` 1 — * `Schedule`
- `Student` 1 — * `Snapshot`
- `AttendanceEvent` * — 0..1 `Snapshot`

**Énumérations :** `EventType {entry, exit}`, `SessionType {session, break}`, `AttendanceStatus {present, late, absent}`, `CrossingDirection {top_to_bottom_is_entry, bottom_to_top_is_entry}`, `CameraSourceType {ip_camera, phone}`.

## 3. Flux d'authentification (réel)

1. Le client appelle `POST /api/v1/auth/login` avec un `OAuth2PasswordRequestForm` (`username` = email, `password`).
2. `authenticate_user` (`crud/user.py`) récupère l'utilisateur par email puis vérifie le mot de passe avec `verify_password` (bcrypt).
3. En cas d'échec → `401`. En cas de succès → `create_access_token(subject=user.email)` génère un JWT `HS256` avec `sub` = email et `exp`.
4. La réponse est un schéma `Token { access_token, token_type="bearer" }`.
5. Pour les routes protégées, `get_current_user` (`core/deps.py`) décode le jeton, extrait le `sub`, recharge l'utilisateur et vérifie `is_active`.
6. Toutes les routes sauf `/auth/login` et `/phone-camera/*` sont protégées.

## 4. Services métier implémentés

| Service | Module | Rôle |
|---------|--------|------|
| **Photos** | `services/photos.py` | Sauvegarde des photos étudiants sur disque sous `PHOTO_STORAGE_DIR/students/{id}.{ext}`. Validation du type (JPEG/PNG/WebP), taille max 8 Mo, protection contre le path traversal. |
| **Email** | `services/email.py` | Envoi du lien d'appairage par `smtplib`. Support STARTTLS (587) et TLS implicite (465). Désactivable (SMTP_HOST vide). |
| **IA faciale** | `services/ai/face_embedding.py` | InsightFace `buffalo_l` (512-dim ArcFace). 4 fonctions : `extract_single_face_embedding` (enrôlement, exactement 1 visage), `extract_all_face_embeddings` (reconnaissance directe, plusieurs visages), `cosine_similarity`, `match_student` (seuil de similarité). Exceptions : `NoFaceDetected`, `MultipleFacesDetected`. |
| **Présence** | `services/attendance/intervals.py` | Reconstruction pure d'intervalles `[entrée, sortie]` : entrées doubles ignorées, sorties orphelines ignorées, sortie manquante = intervalle ouvert. |
| **Présence** | `services/attendance/engine.py` | Fonction pure `compute_session(intervals, window, seuils)` → statut PRESENT/LATE/ABSENT par ratio de chevauchement. |
| **Présence** | `services/attendance/service.py` | Orchestration : lecture des événements → `build_intervals` → `compute_session` par séance → `upsert_result`. Idempotent. |
| **Reconnaissance directe** | `services/attendance/live_recognition.py` | Boucle asynchrone toutes les 3s : pour chaque caméra téléphone active assignée à une séance en cours, capture la dernière frame → extraction des visages → matching → écriture événement ENTRY → calcul présence immédiat. Cache mémoire anti-spam par étudiant/jour. |
| **WebRTC** | `services/camera/webrtc.py` | Gestion de sessions WebRTC (`aiortc`). 4 opérations : `handle_offer`, `get_latest_frame_bgr`, `close_session`, `shutdown_all`. Reaper des sessions périmées (30s). État en mémoire (hypothèse : un seul process uvicorn). |
| **Test connexion** | `services/camera/connection.py` | Teste une caméra IP via OpenCV : `VideoCapture.read()` avec timeout court. |
| **Rapports** | `services/reports/aggregation.py` | Agrégation des `attendance_results` par étudiant sur une période (daily/weekly/monthly). Retourne `Report` avec `StudentReportRow[]`. |
| **Rapports** | `services/reports/exporters.py` | Export du `Report` en CSV (UTF-8 BOM), Excel (openpyxl, en-têtes stylisés), PDF (reportlab, A4, tableau). |

## 5. Routes API complètes

| Route | Méthodes | Authentification | Rôle |
|-------|----------|------------------|------|
| `/api/v1/auth/login` | POST | Non | Connexion admin |
| `/api/v1/auth/me` | GET | Admin | Profil admin courant |
| `/api/v1/students` | GET, POST | Admin | Lister (paginé + recherche) / Créer |
| `/api/v1/students/{pk}` | GET, PUT, DELETE | Admin | Détail / Modifier / Supprimer |
| `/api/v1/students/{pk}/photo` | POST | Admin | Upload photo + enrôlement facial (InsightFace → embedding → pgvector) |
| `/api/v1/students/{pk}/photo` | GET | Admin | Servir la photo |
| `/api/v1/schedules` | GET, POST | Admin | Lister / Créer un créneau |
| `/api/v1/schedules/{pk}` | GET, PUT, DELETE | Admin | Détail / Assigner caméra / Supprimer |
| `/api/v1/events` | POST, GET | Admin | Créer un événement manuel / Lister (filtrable) |
| `/api/v1/attendance/compute` | POST | Admin | Déclencher le calcul de présence pour une date |
| `/api/v1/attendance/results` | GET | Admin | Lister les résultats (filtrable) |
| `/api/v1/dashboard/summary` | GET | Admin | Métriques du tableau de bord (nb étudiants, présents/absents, événements récents) |
| `/api/v1/reports` | GET | Admin | Générer rapport CSV/Excel/PDF (daily/weekly/monthly) |
| `/api/v1/cameras` | GET, POST | Admin | Lister / Créer une caméra |
| `/api/v1/cameras/{pk}` | GET, PUT, DELETE | Admin | Détail / Modifier / Supprimer |
| `/api/v1/cameras/{pk}/test-connection` | POST | Admin | Tester la connexion |
| `/api/v1/cameras/{pk}/send-pairing-email` | POST | Admin | Envoyer le lien d'appairage par email |
| `/api/v1/phone-camera/{token}` | GET | Non | Infos publiques de la caméra téléphone |
| `/api/v1/phone-camera/{token}/offer` | POST | Non | Échange SDP WebRTC (téléphone → serveur) |
| `/api/v1/phone-camera/{token}/stop` | POST | Non | Fermer la session WebRTC |
| `/health` | GET | Non | Santé du backend |

## 6. Ce qui est implémenté vs. prévu

**Implémenté (vérifié dans le code) :**
- Authentification administrateur complète (login + `/auth/me`).
- CRUD étudiants complet + recherche paginée + champ dérivé `has_face_embedding`.
- Enrôlement facial : upload photo → détection InsightFace (exactement 1 visage) → embedding pgvector 512 dim.
- CRUD caméras (IP + téléphone) avec `source_type`, génération automatique de `webrtc_token`, masquage des identifiants dans les réponses.
- Test de connexion caméra IP (OpenCV).
- Lien d'appairage HTTPS + certificat auto-signé avec SAN.
- WebRTC phone camera : échange SDP (offre/réponse), streaming en direct du téléphone vers le serveur via `aiortc`.
- Boucle de reconnaissance en direct : toutes les 3s, frames téléphone → InsightFace → matching → événement ENTRY → calcul présence.
- CRUD emploi du temps : création/suppression de créneaux, assignation de caméra.
- CRUD événements manuels (entrée/sortie).
- Moteur de calcul de présence par séance (intervalles → ratio de chevauchement → PRESENT/LATE/ABSENT).
- Tableau de bord avec métriques et événements récents.
- Rapports avec export CSV, Excel (openpyxl), PDF (reportlab), granularité daily/weekly/monthly.
- Envoi d'email SMTP (lien d'appairage).
- 7 tables ORM et 5 énumérations définies et migrées (5 migrations Alembic).
- Amorçage des données (`initial_data.py`) : admin par défaut + emploi du temps.
- Extension pgvector activée (`init-db/01-extensions.sql`).
- Frontend React complet (TypeScript, Tailwind CSS 4, Vite) avec 9 pages.

**Prévu / non implémenté (structure présente, logique absente) :**
- **Anti-spoofing** (MiniFASNet) — non intégré.
- **Ligne de franchissement virtuelle** en temps réel avec suivi ByteTrack — non implémenté (le modèle `Camera` a les champs mais aucun service ne les exploite).
- **Événements SORTIE automatiques** — la boucle live_recognition ne marque que les ENTRÉES.
- **Snapshots** — la table existe mais n'est pas peuplée par le pipeline actuel.
- **Multi-salles** — un seul emploi du temps fixe pour toutes les caméras.
- **Enrôlement des enseignants** — pas de table `teachers`, stockage localStorage côté frontend uniquement.
- **Notifications temps réel** (websocket) — non implémenté.
