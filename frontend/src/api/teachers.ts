// The backend has no Teacher model/CRUD yet (see frontend/README.md), so this
// module persists teachers client-side only, in localStorage, with the same
// shape the real CRUD endpoint would use once it exists.
import type { Teacher, TeacherCreate } from "../lib/types";

const STORAGE_KEY = "presence.teachers";
// No backend attendance tracking for teachers yet (mirrors the student
// system's limitation: there's no live face-recognition pipeline for anyone
// yet), so presence is a manual per-day toggle stored client-side, keyed by
// ISO date then teacher id. Absent unless explicitly marked present, same
// default as the student attendance engine.
const ATTENDANCE_KEY = "presence.teacher_attendance";

function read(): Teacher[] {
  try {
    const stored: Partial<Teacher>[] = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    // Records created before `photo_data_url` existed have no such key at
    // all (not even `null`); backfill so the field always matches its type.
    return stored.map((t) => ({ photo_data_url: null, ...t }) as Teacher);
  } catch {
    return [];
  }
}

function write(teachers: Teacher[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(teachers));
}

function simulateLatency<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), 150));
}

export async function listTeachers(search?: string): Promise<Teacher[]> {
  let teachers = read();
  if (search) {
    const q = search.toLowerCase();
    teachers = teachers.filter(
      (t) =>
        t.full_name.toLowerCase().includes(q) ||
        t.teacher_id.toLowerCase().includes(q) ||
        (t.department ?? "").toLowerCase().includes(q),
    );
  }
  return simulateLatency(teachers);
}

export async function createTeacher(payload: TeacherCreate): Promise<Teacher> {
  const teachers = read();
  if (teachers.some((t) => t.teacher_id === payload.teacher_id)) {
    throw new Error("A teacher with this ID already exists");
  }
  const teacher: Teacher = { id: crypto.randomUUID(), ...payload };
  write([...teachers, teacher]);
  return simulateLatency(teacher);
}

export async function deleteTeacher(id: string): Promise<void> {
  write(read().filter((t) => t.id !== id));
  return simulateLatency(undefined);
}
