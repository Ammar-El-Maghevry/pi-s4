import { api } from "../lib/api";
import type {
  Camera,
  CameraCreate,
  CameraTestResult,
  CameraUpdate,
  EmailSendResult,
} from "../lib/types";

export async function listCameras(): Promise<Camera[]> {
  const { data } = await api.get<Camera[]>("/cameras", { params: { limit: 500 } });
  return data;
}

export async function createCamera(payload: CameraCreate): Promise<Camera> {
  const { data } = await api.post<Camera>("/cameras", payload);
  return data;
}

export async function updateCamera(id: number, payload: CameraUpdate): Promise<Camera> {
  const { data } = await api.put<Camera>(`/cameras/${id}`, payload);
  return data;
}

export async function deleteCamera(id: number): Promise<void> {
  await api.delete(`/cameras/${id}`);
}

export async function testCameraConnection(id: number): Promise<CameraTestResult> {
  const { data } = await api.post<CameraTestResult>(`/cameras/${id}/test-connection`);
  return data;
}

export async function sendPairingEmail(id: number): Promise<EmailSendResult> {
  const { data } = await api.post<EmailSendResult>(`/cameras/${id}/send-pairing-email`);
  return data;
}
