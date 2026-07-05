import axios, { AxiosError } from "axios";
import { logApiCall } from "./apiLog";
import type { ApiErrorDetail } from "../types/api";

export const TOKEN_STORAGE_KEY = "pi_access_token";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    logApiCall({
      method: (response.config.method ?? "get").toUpperCase(),
      path: response.config.url ?? "",
      status: response.status,
      error: null,
    });
    return response;
  },
  (error: AxiosError<ApiErrorDetail>) => {
    const status = error.response?.status ?? null;
    logApiCall({
      method: (error.config?.method ?? "?").toUpperCase(),
      path: error.config?.url ?? "",
      status,
      error: error.response ? JSON.stringify(error.response.data) : error.message,
    });

    if (status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      if (location.pathname !== "/login") {
        location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

/** Extrait un message lisible d'une réponse d'erreur FastAPI/Pydantic. */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiErrorDetail | undefined;
    const detail = data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg).join(" ; ");
    }
    return error.message;
  }
  return String(error);
}

/** Statut HTTP d'une erreur axios, ou null si absent (erreur réseau). */
export function extractErrorStatus(error: unknown): number | null {
  if (axios.isAxiosError(error)) {
    return error.response?.status ?? null;
  }
  return null;
}
