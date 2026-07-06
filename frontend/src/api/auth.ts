import { api } from "../lib/api";
import type { CurrentUser } from "../lib/types";

export async function login(email: string, password: string): Promise<string> {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const { data } = await api.post<{ access_token: string; token_type: string }>(
    "/auth/login",
    form,
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } },
  );
  return data.access_token;
}

export async function fetchMe(): Promise<CurrentUser> {
  const { data } = await api.get<Omit<CurrentUser, "role">>("/auth/me");
  // The backend only issues admin tokens today; every authenticated user is an admin.
  return { ...data, role: "admin" };
}
