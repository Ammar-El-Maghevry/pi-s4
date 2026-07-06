import axios, { AxiosError } from "axios";

export const TOKEN_STORAGE_KEY = "presence.token";

export const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A 401 means the token is missing/expired/invalid — the session can't be
// recovered client-side, so drop it and force a fresh login instead of
// leaving the user stuck with every request silently failing.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export function apiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError<{ detail?: string | { msg: string }[] }>;
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join(", ");
    if (err.response?.status === 401) return "Session expired, please log in again.";
    if (!err.response) return "Network error — is the backend running?";
    return err.message;
  }
  return "Unexpected error";
}
