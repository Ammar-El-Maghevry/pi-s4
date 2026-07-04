# Diagramme de classes (UML)

Diagramme fidèle au code des modèles ORM (`backend/app/models/*`), des énumérations
(`app/models/enums.py`) et des principaux schémas Pydantic (`app/schemas/*`).
Chaque attribut a été vérifié par rapport à son fichier source. Visibilité `+` = public.

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
    class Token {
        <<schema>>
        +str access_token
        +str token_type
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
    }

    %% ======================= Relations entre entités =======================
    Student "1" -- "*" AttendanceEvent : génère
    Student "1" -- "*" AttendanceResult : concerne
    Schedule "1" -- "*" AttendanceResult : évalue
    Student "1" -- "*" Snapshot : capture
    AttendanceEvent "*" -- "0..1" Snapshot : associé à

    %% ======================= Dépendances aux énumérations =======================
    Schedule ..> SessionType : utilise
    AttendanceEvent ..> EventType : utilise
    AttendanceResult ..> AttendanceStatus : utilise
    Snapshot ..> EventType : utilise

    %% ======================= Liens couche schémas / CRUD -> modèles =======================
    UserCreate ..> User : crée
    UserRead ..> User : projette
    StudentCreate ..> Student : crée
    StudentUpdate ..> Student : met à jour
    StudentRead ..> Student : projette
    CRUD_User ..> User : gère
    CRUD_Student ..> Student : gère
    CRUD_User ..> Token : émet (via JWT)
```

> Note de fidélité : `Optional~type~` représente les types optionnels
> (`str | None`, etc.) du code ; `Vector512` correspond à `Vector(512)` (pgvector).
> Les tables `attendance_events`, `attendance_results` et `snapshots` n'ont
> **pas encore** de couche CRUD/schéma associée dans le code (phases futures).
