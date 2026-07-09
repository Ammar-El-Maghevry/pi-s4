# Diagrammes de séquence (UML)

Participants réels du code : **Client**, **API FastAPI**, **Dépendances/JWT**
(`core/deps.py` + `core/security.py`), **Couche CRUD** (`crud/*`),
**Services** (`services/*`), **Base PostgreSQL**, **InsightFace**,
**aiortc/WebRTC**.

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

## 3. Enrôlement facial (upload photo + embedding) — *implémenté*

Source : `app/api/routes/students.py` (`POST /{pk}/photo`), `app/services/photos.py`,
`app/services/ai/face_embedding.py`, `app/crud/student.py`.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Administrateur
    participant API as API FastAPI<br/>(routes/students.py)
    participant JWT as Dépendances / JWT
    participant CRUD as Couche CRUD<br/>(crud/student.py)
    participant Photo as Service photos<br/>(services/photos.py)
    participant Face as Service IA<br/>(services/ai/face_embedding.py)
    participant DB as Base PostgreSQL

    Client->>API: POST /api/v1/students/{pk}/photo<br/>Authorization: Bearer <jeton><br/>(multipart: image jpeg/png/webp, max 8 Mo)

    Note over API,JWT: get_current_user + get_student
    API->>JWT: get_current_user(token)
    JWT-->>API: administrateur (ou 401)

    API->>CRUD: get_student(db, pk)
    CRUD->>DB: SELECT * FROM students WHERE id = :pk
    DB-->>CRUD: étudiant (ou aucun)
    alt Étudiant introuvable
        API-->>Client: 404
    else Étudiant trouvé
        API->>Photo: save_student_photo(student_id, image_data)
        Note over Photo: valide type MIME, taille,<br/>chemin (anti path traversal)
        Photo-->>API: photo_path

        API->>Face: extract_single_face_embedding(image_bytes)
        Note over Face: InsightFace buffalo_l<br/>exactement 1 visage requis
        alt Aucun visage détecté
            Face-->>API: NoFaceDetected
            API-->>Client: 422 « Aucun visage détecté »
        else Plusieurs visages
            Face-->>API: MultipleFacesDetected
            API-->>Client: 422 « Plusieurs visages détectés »
        else Exactement 1 visage
            Face-->>API: embedding (512 floats)

            API->>CRUD: set_student_photo(db, student, photo_path, embedding)
            CRUD->>DB: UPDATE students SET photo_path, face_embedding
            DB-->>CRUD: étudiant mis à jour
            CRUD-->>API: StudentRead (has_face_embedding=true)

            API-->>Client: 200 StudentRead
        end
    end
```

---

## 4. Calcul de présence — *implémenté*

Source : `app/api/routes/attendance.py`, `app/services/attendance/*`,
`app/crud/attendance_event.py`, `app/crud/attendance_result.py`,
`app/crud/schedule.py`.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Administrateur
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
            Note over Engine: règles : entrées doubles ignorées,<br/>sorties orphelines ignorées,<br/>sortie manquante = intervalle ouvert
            Engine-->>Svc: intervalles [entrée→sortie]

            loop pour chaque séance (SessionType.SESSION)
                Svc->>Engine: compute_session(intervals, window_start, window_end)
                Note over Engine: ratio = chevauchement / durée séance<br/>seuils : present_threshold >= 0.7<br/>late_threshold >= 0.2
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

## 5. Flux caméra téléphone (WebRTC + reconnaissance en direct) — *implémenté*

Source : `app/api/routes/phone_camera.py`, `app/services/camera/webrtc.py`,
`app/services/attendance/live_recognition.py`, `app/services/ai/face_embedding.py`.

```mermaid
sequenceDiagram
    autonumber
    participant Phone as Téléphone<br/>(navigateur)
    participant Pub as API publique<br/>(routes/phone_camera.py)
    participant WebRTC as Service WebRTC<br/>(services/camera/webrtc.py)
    participant CRUD as Couche CRUD
    participant DB as Base PostgreSQL
    participant Admin as Administrateur<br/>(frontend)
    participant Live as Boucle Live<br/>(live_recognition.py)
    participant Face as IA faciale<br/>(face_embedding.py)

    Note over Admin,DB: 0. Admin crée une caméra PHONE
    Admin->>Admin: POST /api/v1/cameras { source_type: "phone", name: "Salle A" }
    Note over Admin,CRUD: Le CRUD génère un webrtc_token aléatoire
    Admin-->>Admin: CameraRead { webrtc_token, pairing_link }

    Note over Admin,Phone: 1. Admin envoie le lien au téléphone<br/>(par email ou copié manuellement)

    Phone->>Pub: GET /api/v1/phone-camera/{token}
    Pub->>CRUD: get_camera_by_token(token)
    CRUD-->>Pub: Camera info
    Pub-->>Phone: PhoneCameraInfo { name, location, is_active }

    Note over Phone: Affiche la page d'appairage<br/>Demande accès caméra (getUserMedia)

    Phone->>Phone: getUserMedia({ video: { facingMode: "environment" } })
    alt Permission refusée
        Phone-->>Phone: message d'erreur
    else Flux obtenu
        Phone->>Pub: POST /phone-camera/{token}/offer<br/>{ sdp: offer_SDP, type: "offer" }
        Pub->>WebRTC: handle_offer(token, sdp, type)
        Note over WebRTC: Crée RTCPeerConnection,<br/>attache le track handler,<br/>génère la réponse SDP
        WebRTC-->>Pub: answer_SDP
        Pub-->>Phone: WebRTCAnswer { sdp: answer_SDP, type: "answer" }

        Note over Phone,WebRTC: Connexion WebRTC établie via STUN<br/>Le téléphone diffuse en direct

        loop Toutes les 3 secondes
            Live->>Live: _tick()
            Live->>CRUD: list_cameras(db, limit=500)
            CRUD-->>Live: [caméras actives]

            loop pour chaque caméra PHONE active
                Live->>Live: _active_session(db, camera_id, now)
                Live->>CRUD: list_schedules(db)
                CRUD-->>Live: séances

                alt Séance en cours assignée à cette caméra
                    Live->>WebRTC: get_latest_frame_bgr(token)
                    WebRTC-->>Live: frame BGR (numpy) ou None

                    alt Frame reçue
                        Live->>Face: extract_all_face_embeddings(frame)
                        Face-->>Live: [embeddings + bboxes]

                        Live->>CRUD: list_face_candidates(db)
                        CRUD-->>Live: [(student_id, embedding)]

                        loop pour chaque visage détecté
                            Live->>Face: match_student(embedding, candidates, threshold)
                            Face-->>Live: (student_id, score) ou None

                            alt Match trouvé et pas déjà marqué aujourd'hui
                                Live->>CRUD: create_event(AttendanceEventCreate(
                                    student_id, ENTRY, confidence, camera_id))
                                CRUD->>DB: INSERT INTO attendance_events
                                Live->>Live: _marked_today[student_id] = today
                                Live->>Live: compute_student_date(db, student_id, today)
                                Live->>DB: COMMIT
                            end
                        end
                    end
                end
            end
        end

        Note over Phone: L'utilisateur appuie sur « Arrêter »
        Phone->>Pub: POST /phone-camera/{token}/stop
        Pub->>WebRTC: close_session(token)
        WebRTC-->>Pub: session fermée
        Pub-->>Phone: 204 No Content
    end
```

---

## 6. Configuration d'une caméra par l'administrateur — *implémenté*

Source : `app/api/routes/cameras.py`, `app/schemas/camera.py`, `app/crud/camera.py`.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Administrateur
    participant API as API FastAPI<br/>(routes/cameras.py)
    participant JWT as Dépendances / JWT<br/>(core/deps.py)
    participant Schema as Schéma Pydantic<br/>(schemas/camera.py)
    participant CRUD as Couche CRUD<br/>(crud/camera.py)
    participant DB as Base PostgreSQL

    Client->>API: POST /api/v1/cameras (ou PUT /cameras/{id})<br/>Authorization: Bearer <jeton><br/>{ name, source_type, source_url?, ligne, seuils... }

    Note over API,JWT: Dépendance get_current_user (protège la route)
    API->>JWT: get_current_user(token)
    JWT-->>API: administrateur courant (ou 401)

    Note over API,Schema: Validation des seuils et source_url
    API->>Schema: valider CameraCreate / CameraUpdate
    alt Seuils hors [0,1] ou present_threshold <= late_threshold
        Schema-->>API: ValidationError
        API-->>Client: 422 Unprocessable Entity
    else source_type=IP_CAMERA et source_url vide
        Schema-->>API: ValidationError
        API-->>Client: 422
    else Données valides
        Schema-->>API: données validées
        API->>CRUD: create_camera / update_camera(db, data)
        Note over CRUD: Pour PHONE : génère webrtc_token aléatoire
        Note over CRUD: Pour IP_CAMERA : utilise source_url fourni
        CRUD->>DB: INSERT / UPDATE cameras
        DB-->>CRUD: caméra enregistrée
        CRUD-->>API: objet Camera
        Note over API,Schema: CameraRead masque le source_url<br/>et calcule pairing_link
        API->>Schema: mask_source_url(source_url)
        API-->>Client: 201 / 200 CameraRead (identifiants masqués)
    end
```

---

## 7. Test de connexion à une caméra — *implémenté*

Source : `app/api/routes/cameras.py`, `app/services/camera/connection.py`.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Administrateur
    participant API as API FastAPI<br/>(routes/cameras.py)
    participant CRUD as Couche CRUD<br/>(crud/camera.py)
    participant DB as Base PostgreSQL
    participant Svc as Service caméra<br/>(services/camera/connection.py)
    participant CV as OpenCV<br/>(import paresseux)

    Client->>API: POST /api/v1/cameras/{id}/test-connection<br/>Authorization: Bearer <jeton>
    Note over API: route protégée par get_current_user

    API->>CRUD: get_camera(db, id)
    CRUD->>DB: SELECT * FROM cameras WHERE id = :id
    DB-->>CRUD: caméra (ou aucune)
    alt Caméra introuvable
        API-->>Client: 404 « Camera introuvable »
    else source_type=PHONE
        Svc-->>API: { success:true, message:"Camera telephone (connexion WebRTC)" }
    else Caméra IP trouvée
        API->>Svc: test_camera_connection(source_url)
        Svc->>CV: import cv2 (au premier appel)
        alt OpenCV non installé
            CV-->>Svc: ImportError
            Svc-->>API: { success:false, message:"OpenCV indisponible" }
        else OpenCV disponible
            Svc->>CV: VideoCapture(source).read() (timeout court)
            alt Flux injoignable / aucune image
                CV-->>Svc: échec
                Svc-->>API: { success:false, message:"..." }
            else Une image lue
                CV-->>Svc: frame (hauteur, largeur)
                Svc-->>API: { success:true, width, height }
            end
        end
        API-->>Client: 200 CameraTestResult
    end
```

---

## 8. Envoi du lien d'appairage par email — *implémenté*

Source : `app/api/routes/cameras.py`, `app/services/email.py`.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Administrateur
    participant API as API FastAPI<br/>(routes/cameras.py)
    participant CRUD as Couche CRUD<br/>(crud/camera.py)
    participant Email as Service email<br/>(services/email.py)
    participant SMTP as Serveur SMTP

    Client->>API: POST /api/v1/cameras/{id}/send-pairing-email<br/>Authorization: Bearer <jeton>
    Note over API: route protégée par get_current_user

    API->>CRUD: get_camera(db, id)
    CRUD-->>API: Camera

    alt Caméra introuvable
        API-->>Client: 404
    else pairing_email absent
        API-->>Client: 400 « Aucune adresse email configurée »
    else SMTP_HOST non configuré
        API-->>Client: 503 « Email désactivé »
    else Tout OK
        API->>Email: send_pairing_email(to_email, pairing_link)
        Email->>SMTP: connexion STARTTLS / TLS
        SMTP-->>Email: authentifié
        Email->>SMTP: ENVOI message HTML
        alt Succès
            SMTP-->>Email: ok
            Email-->>API: True
            API-->>Client: 200 EmailSendResult { success:true }
        else Échec
            SMTP-->>Email: erreur
            Email-->>API: False
            API-->>Client: 200 EmailSendResult { success:false, message:"..." }
        end
    end
```

---

## 9. Génération de rapport — *implémenté*

Source : `app/api/routes/reports.py`, `app/services/reports/aggregation.py`,
`app/services/reports/exporters.py`.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Administrateur
    participant API as API FastAPI<br/>(routes/reports.py)
    participant JWT as Dépendances / JWT
    participant Agg as Service agrégation<br/>(aggregation.py)
    participant Xport as Service export<br/>(exporters.py)
    participant DB as Base PostgreSQL

    Client->>API: GET /api/v1/reports?period=daily&reference=2026-07-09&format=csv<br/>Authorization: Bearer <jeton>

    Note over API,JWT: get_current_user
    API->>JWT: get_current_user(token)
    JWT-->>API: administrateur (ou 401)

    API->>Agg: build_report(db, period, reference)
    Agg->>Agg: period_range(period, reference) -> start, end
    Agg->>DB: SELECT attendance_results + students<br/>WHERE result_date BETWEEN start AND end
    DB-->>Agg: [resultats avec full_name, student_id]

    Note over Agg: Agrège par student_id :<br/>cumul present/late/absent
    Agg-->>API: Report { period, start_date, end_date, rows }

    alt format=csv
        API->>Xport: to_csv(report)
        Xport-->>API: bytes (UTF-8 BOM)
        API-->>Client: 200 text/csv
    else format=xlsx
        API->>Xport: to_excel(report)
        Note over Xport: openpyxl, en-têtes stylisés
        Xport-->>API: bytes
        API-->>Client: 200 application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    else format=pdf
        API->>Xport: to_pdf(report)
        Note over Xport: reportlab, A4, tableau
        Xport-->>API: bytes
        API-->>Client: 200 application/pdf
    end
```

---

## 10. Tableau de bord — *implémenté*

Source : `app/api/routes/dashboard.py`, `app/crud/dashboard.py`.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Administrateur
    participant API as API FastAPI<br/>(routes/dashboard.py)
    participant CRUD as Couche CRUD<br/>(crud/dashboard.py)
    participant DB as Base PostgreSQL

    Client->>API: GET /api/v1/dashboard/summary<br/>Authorization: Bearer <jeton>

    Note over API: route protégée par get_current_user

    par Nombre total d'étudiants
        API->>CRUD: count_students(db)
        CRUD->>DB: SELECT COUNT(*) FROM students
        DB-->>CRUD: 42
        CRUD-->>API: 42
    and Étudiants présents aujourd'hui
        API->>CRUD: count_present_students(db, today)
        CRUD->>DB: SELECT COUNT(*) FROM attendance_results<br/>WHERE result_date = today AND status != 'absent'
        DB-->>CRUD: 35
        CRUD-->>API: 35
    and Événements récents
        API->>CRUD: recent_events(db, limit=10)
        CRUD->>DB: SELECT events + student name<br/>ORDER BY timestamp DESC LIMIT 10
        DB-->>CRUD: [entrées/sorties récentes]
        CRUD-->>API: [RecentEvent]
    end

    API-->>Client: 200 DashboardSummary { date, total_students, present_today, absent_today, recent_events }
```
