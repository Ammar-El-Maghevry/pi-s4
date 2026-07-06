import { api } from "../lib/api";
import type { DashboardSummary } from "../lib/types";

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await api.get<DashboardSummary>("/dashboard/summary");
  return data;
}
