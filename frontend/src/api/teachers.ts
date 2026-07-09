import { api } from "../lib/api";
import type { Teacher, TeacherAttendanceRecord, TeacherCreate } from "../lib/types";

export async function listTeachers(search?: string): Promise<Teacher[]> {
  const { data } = await api.get<Teacher[]>("/teachers", {
    params: { limit: 500, search: search || undefined },
  });
  return data;
}

export async function createTeacher(payload: TeacherCreate): Promise<Teacher> {
  const { data } = await api.post<Teacher>("/teachers", payload);
  return data;
}

export async function deleteTeacher(id: number): Promise<void> {
  await api.delete(`/teachers/${id}`);
}

export async function uploadTeacherPhoto(id: number, photo: Blob): Promise<Teacher> {
  const form = new FormData();
  form.append("file", photo, "photo.jpg");
  const { data } = await api.post<Teacher>(`/teachers/${id}/photo`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function fetchTeacherPhotoUrl(id: number): Promise<string> {
  const { data } = await api.get(`/teachers/${id}/photo`, { responseType: "blob" });
  return URL.createObjectURL(data);
}

export async function listTeacherAttendance(date: string): Promise<TeacherAttendanceRecord[]> {
  const { data } = await api.get<TeacherAttendanceRecord[]>("/teachers/attendance/today", {
    params: { date },
  });
  return data;
}

export async function getTeacherAttendance(date: string): Promise<Record<number, boolean>> {
  const rows = await listTeacherAttendance(date);
  return Object.fromEntries(rows.map((row) => [row.teacher_id, row.is_present]));
}

export async function setTeacherPresent(
  teacherId: number,
  date: string,
  present: boolean,
): Promise<void> {
  await api.put(`/teachers/${teacherId}/attendance`, { is_present: present }, { params: { date } });
}
