# Diagramme de classes (UML) — Modèles ORM

Seules les 7 tables de la base de données sont représentées. Fidèle au code réel :
`backend/app/models/*`.

```mermaid
classDiagram
    direction LR

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
    Student "1" -- "*" Snapshot : capture
    Schedule "1" -- "*" AttendanceResult : évalue
    Schedule "*" -- "0..1" Camera : assignée à
    AttendanceEvent "*" -- "0..1" Snapshot : associé à
```

> `Optional~type~` représente les types optionnels (`str | None`, etc.) du code.
> `Vector512` = `Vector(512)` (pgvector). Les énumérations
> (`EventType`, `SessionType`, `AttendanceStatus`, `CrossingDirection`,
> `CameraSourceType`) sont stockées en base comme `Enum` PostgreSQL.
