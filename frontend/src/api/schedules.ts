// Real schedule rows come from the backend (read-only: session_number, name,
// start_time, end_time, session_type). The backend has no `teacher`/`room`/
// `day`/check-in/check-out-offset fields and no create endpoint yet (see
// frontend/README.md), so those are layered on top client-side, in
// localStorage, keyed by schedule id. New "class plans" created from the UI
// are stored fully client-side with a negative local id.
import { api } from "../lib/api";
import type { Schedule, ScheduleExtras, ScheduleWithExtras } from "../lib/types";
import { SessionType } from "../lib/types";

const EXTRAS_KEY = "presence.schedule_extras";
const LOCAL_SCHEDULES_KEY = "presence.local_schedules";

const DEFAULT_EXTRAS: ScheduleExtras = {
  teacher: "Unassigned",
  room: "TBD",
  day: "Monday",
  check_in_offset_minutes: 15,
  check_out_offset_minutes: 15,
};

function readExtras(): Record<number, ScheduleExtras> {
  try {
    return JSON.parse(localStorage.getItem(EXTRAS_KEY) ?? "{}");
  } catch {
    return {};
  }
}

function writeExtras(extras: Record<number, ScheduleExtras>): void {
  localStorage.setItem(EXTRAS_KEY, JSON.stringify(extras));
}

function readLocalSchedules(): Schedule[] {
  try {
    return JSON.parse(localStorage.getItem(LOCAL_SCHEDULES_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function writeLocalSchedules(schedules: Schedule[]): void {
  localStorage.setItem(LOCAL_SCHEDULES_KEY, JSON.stringify(schedules));
}

export interface ClassPlanInput {
  name: string;
  teacher: string;
  room: string;
  day: string;
  start_time: string;
  end_time: string;
  check_in_offset_minutes: number;
  check_out_offset_minutes: number;
}

export async function listClassPlans(): Promise<ScheduleWithExtras[]> {
  const { data } = await api.get<Schedule[]>("/schedules");
  const extras = readExtras();
  const remote: ScheduleWithExtras[] = data
    .filter((s) => s.session_type === SessionType.SESSION)
    .map((s) => ({ ...s, ...(extras[s.id] ?? DEFAULT_EXTRAS), isLocalOnly: false }));

  const local: ScheduleWithExtras[] = readLocalSchedules().map((s) => ({
    ...s,
    ...(extras[s.id] ?? DEFAULT_EXTRAS),
    isLocalOnly: true,
  }));

  return [...remote, ...local];
}

export async function createClassPlan(input: ClassPlanInput): Promise<ScheduleWithExtras> {
  const localSchedules = readLocalSchedules();
  const nextId = -(localSchedules.length + 1);
  const schedule: Schedule = {
    id: nextId,
    session_number: 0,
    name: input.name,
    start_time: input.start_time,
    end_time: input.end_time,
    session_type: SessionType.SESSION,
    camera_id: null,
    camera: null,
  };
  writeLocalSchedules([...localSchedules, schedule]);

  const extras = readExtras();
  const scheduleExtras: ScheduleExtras = {
    teacher: input.teacher,
    room: input.room,
    day: input.day,
    check_in_offset_minutes: input.check_in_offset_minutes,
    check_out_offset_minutes: input.check_out_offset_minutes,
  };
  extras[nextId] = scheduleExtras;
  writeExtras(extras);

  return { ...schedule, ...scheduleExtras, isLocalOnly: true };
}

export async function assignScheduleCamera(
  scheduleId: number,
  cameraId: number | null,
): Promise<Schedule> {
  const { data } = await api.put<Schedule>(`/schedules/${scheduleId}`, { camera_id: cameraId });
  return data;
}
