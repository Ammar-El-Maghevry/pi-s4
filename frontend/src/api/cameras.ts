import { apiClient } from "./client";
import type { CameraCreate, CameraRead, CameraTestResult, CameraUpdate } from "../types/api";

export async function listCameras(): Promise<CameraRead[]> {
  const { data } = await apiClient.get<CameraRead[]>("/api/v1/cameras");
  return data;
}

export async function createCamera(payload: CameraCreate): Promise<CameraRead> {
  const { data } = await apiClient.post<CameraRead>("/api/v1/cameras", payload);
  return data;
}

export async function updateCamera(id: number, payload: CameraUpdate): Promise<CameraRead> {
  const { data } = await apiClient.put<CameraRead>(`/api/v1/cameras/${id}`, payload);
  return data;
}

export async function deleteCamera(id: number): Promise<void> {
  await apiClient.delete(`/api/v1/cameras/${id}`);
}

export async function testCameraConnection(id: number): Promise<CameraTestResult> {
  const { data } = await apiClient.post<CameraTestResult>(`/api/v1/cameras/${id}/test-connection`);
  return data;
}
