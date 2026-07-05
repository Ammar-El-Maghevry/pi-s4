import { apiClient } from "./client";
import type { StudentCreate, StudentRead, StudentUpdate } from "../types/api";

export async function listStudents(): Promise<StudentRead[]> {
  const { data } = await apiClient.get<StudentRead[]>("/api/v1/students");
  return data;
}

export async function createStudent(payload: StudentCreate): Promise<StudentRead> {
  const { data } = await apiClient.post<StudentRead>("/api/v1/students", payload);
  return data;
}

export async function updateStudent(id: number, payload: StudentUpdate): Promise<StudentRead> {
  const { data } = await apiClient.put<StudentRead>(`/api/v1/students/${id}`, payload);
  return data;
}

export async function deleteStudent(id: number): Promise<void> {
  await apiClient.delete(`/api/v1/students/${id}`);
}
