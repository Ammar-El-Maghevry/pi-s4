// Types mirroring the FastAPI backend's Pydantic schemas exactly (field names/shapes).

export type Role = "admin" | "teacher" | "student";

export interface CurrentUser {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  role: Role;
}

export interface Student {
  id: number;
  full_name: string;
  student_id: string;
  email: string | null;
  department: string | null;
  // Auto-assigned server-side from `department`, batched every 40 students
  // (e.g. "Computer Science 1") — not directly settable.
  class_name: string | null;
  photo_path: string | null;
  has_face_embedding: boolean;
  created_at: string;
  updated_at: string;
}

export interface StudentCreate {
  full_name: string;
  student_id: string;
  email?: string | null;
  department?: string | null;
}

export type StudentUpdate = Partial<StudentCreate>;

export const SessionType = {
  SESSION: "session",
  BREAK: "break",
} as const;
export type SessionType = (typeof SessionType)[keyof typeof SessionType];

export const CrossingDirection = {
  TOP_TO_BOTTOM_IS_ENTRY: "top_to_bottom_is_entry",
  BOTTOM_TO_TOP_IS_ENTRY: "bottom_to_top_is_entry",
} as const;
export type CrossingDirection = (typeof CrossingDirection)[keyof typeof CrossingDirection];

export const CameraSourceType = {
  IP_CAMERA: "ip_camera",
  PHONE: "phone",
} as const;
export type CameraSourceType = (typeof CameraSourceType)[keyof typeof CameraSourceType];

export interface Camera {
  id: number;
  name: string;
  location: string | null;
  source_type: CameraSourceType;
  source_url: string;
  webrtc_token: string | null;
  pairing_email: string | null;
  pairing_link: string | null;
  is_active: boolean;
  line_x1: number | null;
  line_y1: number | null;
  line_x2: number | null;
  line_y2: number | null;
  crossing_direction: CrossingDirection;
  min_crossing_frames: number;
  cooldown_seconds: number;
  present_threshold: number;
  late_threshold: number;
  face_match_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface CameraCreate {
  name: string;
  location?: string | null;
  source_type?: CameraSourceType;
  source_url?: string;
  pairing_email?: string | null;
  is_active?: boolean;
}

export type CameraUpdate = Partial<CameraCreate>;

export interface CameraTestResult {
  success: boolean;
  message: string;
  width: number | null;
  height: number | null;
}

export interface EmailSendResult {
  success: boolean;
  message: string;
}

export interface PhoneCameraInfo {
  name: string;
  location: string | null;
  is_active: boolean;
}

export interface WebRTCOffer {
  sdp: string;
  type: string;
}

export interface WebRTCAnswer {
  sdp: string;
  type: string;
}

export interface Schedule {
  id: number;
  session_number: number;
  name: string;
  start_time: string;
  end_time: string;
  session_type: SessionType;
  camera_id: number | null;
  camera: Camera | null;
}

export const EventType = {
  ENTRY: "entry",
  EXIT: "exit",
} as const;
export type EventType = (typeof EventType)[keyof typeof EventType];

export interface AttendanceEvent {
  id: number;
  student_id: number;
  event_type: EventType;
  timestamp: string;
  confidence: number | null;
  camera_id: string | null;
  snapshot_id: number | null;
}

export const AttendanceStatus = {
  PRESENT: "present",
  LATE: "late",
  ABSENT: "absent",
} as const;
export type AttendanceStatus = (typeof AttendanceStatus)[keyof typeof AttendanceStatus];

export interface AttendanceResult {
  id: number;
  student_id: number;
  schedule_id: number;
  result_date: string;
  status: AttendanceStatus;
  entry_time: string | null;
  exit_time: string | null;
  computed_at: string;
}

export interface RecentEvent {
  id: number;
  student_id: number;
  student_name: string;
  event_type: EventType;
  timestamp: string;
}

export interface DashboardSummary {
  date: string;
  total_students: number;
  present_today: number;
  absent_today: number;
  recent_events: RecentEvent[];
}

// --- Not yet backed by the real API (see frontend/README.md) ---
// Teachers have no backend model/CRUD yet; persisted client-side only.
export interface Teacher {
  id: string;
  full_name: string;
  teacher_id: string;
  email: string | null;
  department: string | null;
  // No backend photo storage for teachers yet, so this is a data: URL stored
  // directly in localStorage alongside the rest of the record.
  photo_data_url: string | null;
}

export type TeacherCreate = Omit<Teacher, "id">;

// Schedules have no `teacher`/`room`/`day`/offset fields or create endpoint yet;
// these are layered on top of the real schedule rows, client-side only.
export interface ScheduleExtras {
  teacher: string;
  room: string;
  day: string;
  check_in_offset_minutes: number;
  check_out_offset_minutes: number;
}

export interface ScheduleWithExtras extends Schedule, ScheduleExtras {
  isLocalOnly: boolean;
}
