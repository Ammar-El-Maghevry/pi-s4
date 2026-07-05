import { apiClient } from "./client";
import type { Token, UserRead } from "../types/api";

/**
 * Le backend attend un formulaire OAuth2 (`application/x-www-form-urlencoded`)
 * avec les champs `username`/`password` — pas du JSON. Voir
 * app/api/routes/auth.py::login (OAuth2PasswordRequestForm).
 */
export async function login(email: string, password: string): Promise<Token> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  const { data } = await apiClient.post<Token>("/api/v1/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function fetchMe(): Promise<UserRead> {
  const { data } = await apiClient.get<UserRead>("/api/v1/auth/me");
  return data;
}
