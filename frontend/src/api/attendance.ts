import { api } from "../lib/api";
import type { AttendanceResult } from "../lib/types";

export interface AttendanceResultsFilter {
  student_id?: number;
  date?: string;
  schedule_id?: number;
}

export async function listAttendanceResults(
  filter: AttendanceResultsFilter = {},
): Promise<AttendanceResult[]> {
  const { data } = await api.get<AttendanceResult[]>("/attendance/results", {
    params: { ...filter, limit: 1000 },
  });
  return data;
}
