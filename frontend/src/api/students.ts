import { api } from "../lib/api";
import type { Student, StudentCreate, StudentUpdate } from "../lib/types";

export async function listStudents(search?: string): Promise<Student[]> {
  const { data } = await api.get<Student[]>("/students", {
    params: { limit: 500, search: search || undefined },
  });
  return data;
}

export async function createStudent(payload: StudentCreate): Promise<Student> {
  const { data } = await api.post<Student>("/students", payload);
  return data;
}

export async function updateStudent(id: number, payload: StudentUpdate): Promise<Student> {
  const { data } = await api.put<Student>(`/students/${id}`, payload);
  return data;
}

export async function deleteStudent(id: number): Promise<void> {
  await api.delete(`/students/${id}`);
}

export async function uploadStudentPhoto(id: number, photo: Blob): Promise<Student> {
  const form = new FormData();
  form.append("file", photo, "photo.jpg");
  const { data } = await api.post<Student>(`/students/${id}/photo`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function fetchStudentPhotoUrl(id: number): Promise<string> {
  const { data } = await api.get(`/students/${id}/photo`, { responseType: "blob" });
  return URL.createObjectURL(data);
}
