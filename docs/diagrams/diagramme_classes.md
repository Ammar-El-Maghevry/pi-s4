# Diagramme de classes (UML)

Diagramme fidèle au code réel : modèles ORM (`backend/app/models/*`), énumérations
(`app/models/enums.py`), schémas Pydantic (`app/schemas/*`), couche CRUD
(`app/crud/*`) et services métier (`app/services/*`). Chaque attribut / signature a
été vérifié par rapport à son fichier source. Visibilité `+` = public.

Les classes marquées `<<future>>` correspondent aux composants non implémentés
(anti-spoofing, ligne de franchissement temps réel, suivi ByteTrack).

```mermaid
classDiagram
    direction LR

    %% ======================= Énumérations =======================
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
    class CrossingDirection {
        <<enumeration>>
        TOP_TO_BOTTOM_IS_ENTRY
        BOTTOM_TO_TOP_IS_ENTRY
    }
    class CameraSourceType {
        <<enumeration>>
        IP_CAMERA
        PHONE
    }

    %% ======================= Modèles ORM =======================
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
        +Optional~int~ camera_id
    }
    class Camera {
        <<table cameras>>
        +int id
        +str name
        +Optional~str~ location
        +CameraSourceType source_type
        +str source_url
        +Optional~str~ webrtc_token
        +Optional~str~ pairing_email
        +bool is_active
        +Optional~int~ line_x1
        +Optional~int~ line_y1
        +Optional~int~ line_x2
        +Optional~int~ line_y2
        +CrossingDirection crossing_direction
        +int min_crossing_frames
        +int cooldown_seconds
        +float present_threshold
        +float late_threshold
        +float face_match_threshold
        +datetime created_at
        +datetime updated_at
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
        +uq_presence_unique(student_id, schedule_id, result_date)
    }
    class Snapshot {
        <<table snapshots>>
        +int id
        +Optional~int~ student_id
        +str image_path
        +EventType event_type
        +datetime captured_at
    }

    %% ======================= Schémas Pydantic =======================
    class UserCreate {
        <<schema>>
        +EmailStr email
        +str full_name
        +str password
    }
    class UserRead {
        <<schema>>
        +int id
        +EmailStr email
        +str full_name
        +bool is_active
        +datetime created_at
    }
    class Token {
        <<schema>>
        +str access_token
        +str token_type
    }
    class StudentCreate {
        <<schema>>
        +str full_name
        +str student_id
        +Optional~EmailStr~ email
        +Optional~str~ department
    }
    class StudentUpdate {
        <<schema>>
        +Optional~str~ full_name
        +Optional~str~ student_id
        +Optional~EmailStr~ email
        +Optional~str~ department
    }
    class StudentRead {
        <<schema>>
        +int id
        +str full_name
        +str student_id
        +Optional~EmailStr~ email
        +Optional~str~ department
        +Optional~str~ photo_path
        +bool has_face_embedding
        +datetime created_at
        +datetime updated_at
    }
    class ScheduleCreate {
        <<schema>>
        +str name
        +Time start_time
        +Time end_time
    }
    class ScheduleUpdate {
        <<schema>>
        +Optional~int~ camera_id
    }
    class ScheduleRead {
        <<schema>>
        +int id
        +int session_number
        +str name
        +Time start_time
        +Time end_time
        +SessionType session_type
        +Optional~int~ camera_id
        +Optional~CameraRead~ camera
    }
    class AttendanceEventCreate {
        <<schema>>
        +int student_id
        +EventType event_type
        +Optional~datetime~ timestamp
        +Optional~float~ confidence
        +Optional~str~ camera_id
    }
    class AttendanceEventRead {
        <<schema>>
        +int id
        +int student_id
        +EventType event_type
        +datetime timestamp
        +Optional~float~ confidence
        +Optional~str~ camera_id
        +Optional~int~ snapshot_id
    }
    class AttendanceResultRead {
        <<schema>>
        +int id
        +int student_id
        +int schedule_id
        +date result_date
        +AttendanceStatus status
        +Optional~datetime~ entry_time
        +Optional~datetime~ exit_time
        +datetime computed_at
    }
    class ComputeReportRead {
        <<schema>>
        +date result_date
        +int students_processed
        +int sessions_per_student
        +int results_written
    }
    class RecentEvent {
        <<schema>>
        +int id
        +int student_id
        +str student_name
        +EventType event_type
        +datetime timestamp
    }
    class DashboardSummary {
        <<schema>>
        +date date
        +int total_students
        +int present_today
        +int absent_today
        +list~RecentEvent~ recent_events
    }
    class CameraCreate {
        <<schema>>
        +str name
        +Optional~str~ location
        +CameraSourceType source_type
        +Optional~str~ source_url
        +Optional~EmailStr~ pairing_email
        +bool is_active
        +Optional~int~ line_x1..line_y2
        +CrossingDirection crossing_direction
        +int min_crossing_frames
        +int cooldown_seconds
        +float present_threshold
        +float late_threshold
        +float face_match_threshold
    }
    class CameraUpdate {
        <<schema>>
        +Optional~str~ name
        +Optional~str~ location
        +Optional~CameraSourceType~ source_type
        +Optional~str~ source_url
        +Optional~EmailStr~ pairing_email
        +Optional~bool~ is_active
        +Optional~int~ line_x1..line_y2
        +Optional~CrossingDirection~ crossing_direction
        +Optional~int~ min_crossing_frames
        +Optional~int~ cooldown_seconds
        +Optional~float~ present_threshold
        +Optional~float~ late_threshold
        +Optional~float~ face_match_threshold
    }
    class CameraRead {
        <<schema>>
        +int id
        +str name
        +Optional~str~ location
        +CameraSourceType source_type
        +str source_url_masquee
        +Optional~str~ webrtc_token
        +Optional~str~ pairing_email
        +Optional~str~ pairing_link
        +bool is_active
        +Optional~int~ line_x1..line_y2
        +CrossingDirection crossing_direction
        +int min_crossing_frames
        +int cooldown_seconds
        +float present_threshold
        +float late_threshold
        +float face_match_threshold
        +datetime created_at
        +datetime updated_at
    }
    class CameraTestResult {
        <<schema>>
        +bool success
        +str message
        +Optional~int~ width
        +Optional~int~ height
    }
    class PhoneCameraInfo {
        <<schema>>
        +str name
        +Optional~str~ location
        +bool is_active
    }
    class WebRTCOffer {
        <<schema>>
        +str sdp
        +str type
    }
    class WebRTCAnswer {
        <<schema>>
        +str sdp
        +str type
    }
    class EmailSendResult {
        <<schema>>
        +bool success
        +str message
    }

    %% ======================= Couche CRUD =======================
    class CRUD_User {
        <<crud user>>
        +get_user_by_email(db, email) User
        +create_user(db, data) User
        +authenticate_user(db, email, password) User
    }
    class CRUD_Student {
        <<crud student>>
        +get_student(db, pk) Student
        +get_student_by_matricule(db, student_id) Student
        +list_students(db, skip, limit, search) list~Student~
        +create_student(db, data) Student
        +update_student(db, student, data) Student
        +delete_student(db, student) None
        +set_student_photo(db, student, image_data) Student
        +list_face_candidates(db) list~tuple~
    }
    class CRUD_Schedule {
        <<crud schedule>>
        +list_schedules(db) list~Schedule~
        +create_schedule(db, data) Schedule
        +get_schedule(db, pk) Schedule
        +update_schedule(db, schedule, data) Schedule
        +delete_schedule(db, schedule) None
    }
    class CRUD_AttendanceEvent {
        <<crud attendance_event>>
        +create_event(db, data) AttendanceEvent
        +list_events(db, student_id, on_date, skip, limit) list~AttendanceEvent~
        +get_events_for_student_on_date(db, student_id, on_date) list~AttendanceEvent~
        +distinct_student_ids_with_events_on_date(db, on_date) list~int~
    }
    class CRUD_AttendanceResult {
        <<crud attendance_result>>
        +upsert_result(db, student_id, schedule_id, result_date, status, entry_time, exit_time) AttendanceResult
        +list_results(db, student_id, on_date, schedule_id, skip, limit) list~AttendanceResult~
    }
    class CRUD_Dashboard {
        <<crud dashboard>>
        +count_students(db) int
        +count_present_students(db, on_date) int
        +recent_events(db, limit) list
    }
    class CRUD_Camera {
        <<crud camera>>
        +get_camera(db, pk) Camera
        +get_camera_by_token(db, token) Camera
        +list_cameras(db, skip, limit) list~Camera~
        +create_camera(db, data) Camera
        +update_camera(db, camera, data) Camera
        +delete_camera(db, camera) None
    }

    %% ======================= Services métier =======================
    class PhotoService {
        <<service photos>>
        +save_student_photo(student_id, image_data) str
        +get_student_photo_path(student_id) str
        +delete_student_photo(student_id) None
        -_validate_content_type(data) None
        -_sanitize_filename(name) str
    }
    class EmailService {
        <<service email>>
        +send_pairing_email(to_email, pairing_link) bool
    }
    class Interval {
        <<service attendance>>
        +datetime start
        +Optional~datetime~ end
    }
    class SessionComputation {
        <<service attendance>>
        +AttendanceStatus status
        +float overlap_ratio
        +float overlap_seconds
        +Optional~datetime~ entry_time
        +Optional~datetime~ exit_time
    }
    class ComputeReport {
        <<service attendance>>
        +date result_date
        +int students_processed
        +int sessions_per_student
        +int results_written
    }
    class AttendanceEngine {
        <<service attendance>>
        +build_intervals(events) list~Interval~
        +compute_session(intervals, window_start, window_end, present_threshold, late_threshold) SessionComputation
        +compute_student_date(db, student_id, on_date) int
        +compute_date(db, on_date, student_id) ComputeReport
    }
    class LiveRecognition {
        <<service attendance>>
        +start() None
        +stop() None
        -_tick() None
        -_process_camera(db, camera, now) None
        -_active_session(db, camera_id, now) Schedule
    }
    class CameraConnectionService {
        <<service camera>>
        +test_camera_connection(source_url, timeout_ms) ConnectionResult
    }
    class WebRTCSessionManager {
        <<service camera>>
        +handle_offer(token, sdp, type) tuple~str, str~
        +get_latest_frame_bgr(token) ndarray
        +get_status(token) ConnectionResult
        +close_session(token) None
        +shutdown_all() None
    }
    class StudentReportRow {
        <<service reports>>
        +int student_id
        +str student_name
        +str matricule
        +int present
        +int late
        +int absent
        +float attendance_rate
    }
    class Report {
        <<service reports>>
        +ReportPeriod period
        +date start_date
        +date end_date
        +list~StudentReportRow~ rows
        +str title
    }
    class ReportsService {
        <<service reports>>
        +period_range(period, reference) tuple
        +build_report(db, period, reference) Report
        +to_csv(report) bytes
        +to_excel(report) bytes
        +to_pdf(report) bytes
    }
    class FaceEmbeddingService {
        <<service ai>>
        +extract_single_face_embedding(image_bytes) list~float~
        +extract_all_face_embeddings(frame) list~FaceEmbedding~
        +cosine_similarity(a, b) float
        +match_student(embedding, candidates, threshold) tuple
    }

    %% ============ Composants futurs (non implémentés) ============
    class Tracker {
        <<future>>
        +update(detections) list~Track~
    }
    class SpoofDetector {
        <<future>>
        +is_live(face_image) bool
    }
    class LineCrossingAnalyzer {
        <<future>>
        +update(track_id, center_xy, at) AttendanceEvent
    }

    %% ======================= Relations entre entités =======================
    Student "1" -- "*" AttendanceEvent : génère
    Student "1" -- "*" AttendanceResult : concerne
    Student "1" -- "*" Snapshot : capture
    Schedule "1" -- "*" AttendanceResult : évalue
    Schedule "*" -- "0..1" Camera : assignée à
    AttendanceEvent "*" -- "0..1" Snapshot : associé à
    %% Lien logique (pas une FK) : attendance_events.camera_id est une chaîne.
    Camera "1" ..> "*" AttendanceEvent : identifie (via camera_id)

    %% ======================= Dépendances aux énumérations =======================
    Schedule ..> SessionType : utilise
    AttendanceEvent ..> EventType : utilise
    AttendanceResult ..> AttendanceStatus : utilise
    Snapshot ..> EventType : utilise
    Camera ..> CrossingDirection : utilise
    Camera ..> CameraSourceType : utilise

    %% ======================= Schémas -> modèles =======================
    UserCreate ..> User : crée
    UserRead ..> User : projette
    StudentCreate ..> Student : crée
    StudentUpdate ..> Student : met à jour
    StudentRead ..> Student : projette
    ScheduleCreate ..> Schedule : crée
    ScheduleUpdate ..> Schedule : met à jour
    ScheduleRead ..> Schedule : projette
    ScheduleRead ..> CameraRead : intègre
    AttendanceEventCreate ..> AttendanceEvent : crée
    AttendanceEventRead ..> AttendanceEvent : projette
    AttendanceResultRead ..> AttendanceResult : projette
    CameraCreate ..> Camera : crée
    CameraUpdate ..> Camera : met à jour
    CameraRead ..> Camera : projette (source_url masquée)
    CRUD_User ..> User : gère
    CRUD_User ..> Token : émet (via JWT)
    CRUD_Student ..> Student : gère
    CRUD_Schedule ..> Schedule : gère
    CRUD_AttendanceEvent ..> AttendanceEvent : gère
    CRUD_AttendanceResult ..> AttendanceResult : gère
    CRUD_Dashboard ..> DashboardSummary : alimente
    CRUD_Camera ..> Camera : gère
    CameraConnectionService ..> Camera : teste le flux
    CameraConnectionService ..> CameraTestResult : produit
    WebRTCSessionManager ..> PhoneCameraInfo : expose
    WebRTCSessionManager ..> WebRTCOffer : reçoit
    WebRTCSessionManager ..> WebRTCAnswer : produit
    EmailService ..> EmailSendResult : produit

    %% ======================= Dépendances des services =======================
    AttendanceEngine ..> Interval : construit
    AttendanceEngine ..> SessionComputation : produit
    AttendanceEngine ..> ComputeReport : produit
    AttendanceEngine ..> CRUD_AttendanceEvent : lit
    AttendanceEngine ..> CRUD_AttendanceResult : écrit
    AttendanceEngine ..> CRUD_Schedule : lit
    LiveRecognition ..> FaceEmbeddingService : détecte
    LiveRecognition ..> WebRTCSessionManager : lit frame
    LiveRecognition ..> CRUD_Student : candidats
    LiveRecognition ..> CRUD_AttendanceEvent : écrit
    LiveRecognition ..> AttendanceEngine : déclenche
    LiveRecognition ..> CRUD_Camera : liste
    LiveRecognition ..> CRUD_Schedule : séance active
    ReportsService ..> Report : produit
    Report ..> StudentReportRow : contient
    PhotoService ..> Student : sauvegarde
    FaceEmbeddingService ..> Student : embedding

    %% ============ Chaîne des composants futurs ============
    FaceEmbeddingService ..> Tracker : alimenterait
    Tracker ..> SpoofDetector : alimenterait
    SpoofDetector ..> FaceEmbeddingService : reconnaîtrait
    FaceEmbeddingService ..> LineCrossingAnalyzer : alimenterait
    LineCrossingAnalyzer ..> Camera : lit la config (ligne, sens, seuils)
    LineCrossingAnalyzer ..> AttendanceEvent : émettrait
```

> **Notes de fidélité**
> - `Optional~type~` représente les types optionnels (`str | None`, etc.) du code ;
>   `Vector512` correspond à `Vector(512)` (pgvector).
> - `AttendanceEngine`, `LiveRecognition`, `ReportsService`, `PhotoService`,
>   `EmailService`, `FaceEmbeddingService`, `CameraConnectionService`,
>   `WebRTCSessionManager` sont des **regroupements logiques** de fonctions de
>   module (pas des classes réelles), représentés ainsi pour la lisibilité du
>   diagramme.
> - Les classes `<<future>>` décrivent les composants **non encore implémentés** :
>   suivi ByteTrack, anti-spoofing MiniFASNet, et analyse de ligne de
>   franchissement en temps réel. L'implémentation actuelle contourne ces
>   composants avec `LiveRecognition` (détection + matching direct sur
>   visages, sans suivi ni ligne).
> - La table `schedules` a désormais une FK `camera_id` vers `cameras`.
> - `CameraRead` calcule `pairing_link` côté serveur à partir de
>   `PHONE_PAIRING_BASE_URL`.
> - `ReportPeriod` n'est pas une énumération de la base de données mais une
>   Enum Python du service de rapports (daily/weekly/monthly).
