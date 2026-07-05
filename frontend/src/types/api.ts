// Types miroir des schémas Pydantic du backend (voir /openapi.json).

export interface Token {
  access_token: string;
  token_type: string;
}

export interface UserRead {
  email: string;
  full_name: string;
  id: number;
  is_active: boolean;
  created_at: string;
}

export interface StudentRead {
  full_name: string;
  student_id: string;
  email: string | null;
  department: string | null;
  id: number;
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

export interface StudentUpdate {
  full_name?: string | null;
  student_id?: string | null;
  email?: string | null;
  department?: string | null;
}

export type CrossingDirection = "top_to_bottom_is_entry" | "bottom_to_top_is_entry";

export interface CameraRead {
  id: number;
  name: string;
  location: string | null;
  source_url: string; // masqué par le backend (rtsp://***:***@host/...)
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
  source_url: string;
  is_active?: boolean;
  line_x1?: number | null;
  line_y1?: number | null;
  line_x2?: number | null;
  line_y2?: number | null;
  crossing_direction?: CrossingDirection;
  min_crossing_frames?: number;
  cooldown_seconds?: number;
  present_threshold?: number;
  late_threshold?: number;
  face_match_threshold?: number;
}

// Champs modifiables depuis le panneau caméra (sous-ensemble volontaire :
// on n'expose pas encore l'édition de la ligne de franchissement dans l'UI).
export interface CameraUpdate {
  name?: string;
  location?: string | null;
  source_url?: string;
  is_active?: boolean;
  present_threshold?: number;
  late_threshold?: number;
  face_match_threshold?: number;
}

export interface CameraTestResult {
  success: boolean;
  message: string;
  width: number | null;
  height: number | null;
}

// Forme du corps d'erreur FastAPI/Pydantic : `detail` est soit une chaîne
// (HTTPException manuelle), soit un tableau d'erreurs de validation Pydantic.
export interface ApiErrorDetail {
  detail?: string | Array<{ msg: string; loc?: (string | number)[] }>;
}
