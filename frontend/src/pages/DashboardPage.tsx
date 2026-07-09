import { useEffect, useState } from "react";
import { fetchDashboardSummary } from "../api/dashboard";
import { listAttendanceResults } from "../api/attendance";
import { listClassPlans } from "../api/schedules";
import { getTeacherAttendance, listTeachers } from "../api/teachers";
import { StatCard } from "../components/StatCard";
import { TableEmpty, TableLoading } from "../components/TableStates";
import { useToast } from "../context/ToastContext";
import { apiErrorMessage } from "../lib/api";
import { formatTime, nowMinutes, timeStringToMinutes, todayIso } from "../lib/time";
import {
  AttendanceStatus,
  type DashboardSummary,
  type ScheduleWithExtras,
  type Teacher,
} from "../lib/types";

const POLL_INTERVAL_MS = 20_000;

export function DashboardPage() {
  const { showError } = useToast();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [schedules, setSchedules] = useState<ScheduleWithExtras[]>([]);
  const [presentBySchedule, setPresentBySchedule] = useState<Record<number, number>>({});
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [teacherAttendance, setTeacherAttendance] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);

  async function load() {
    try {
      const [summaryData, scheduleData, results, teacherData, teacherAttendanceData] =
        await Promise.all([
          fetchDashboardSummary(),
          listClassPlans(),
          listAttendanceResults({ date: todayIso() }),
          listTeachers(),
          getTeacherAttendance(todayIso()),
        ]);
      setSummary(summaryData);
      setSchedules(scheduleData);
      setTeachers(teacherData);
      setTeacherAttendance(teacherAttendanceData);
      const counts: Record<number, number> = {};
      for (const result of results) {
        if (result.status === AttendanceStatus.PRESENT || result.status === AttendanceStatus.LATE) {
          counts[result.schedule_id] = (counts[result.schedule_id] ?? 0) + 1;
        }
      }
      setPresentBySchedule(counts);
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const now = nowMinutes();
  const activeSessions = schedules.filter(
    (s) => timeStringToMinutes(s.start_time) <= now && now <= timeStringToMinutes(s.end_time),
  ).length;
  const teachersPresent = teachers.filter((t) => teacherAttendance[t.id]).length;
  const teachersAbsent = teachers.length - teachersPresent;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-text-muted">Live overview of today's attendance</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Students enrolled" value={summary?.total_students ?? "—"} />
        <StatCard label="Present now" value={summary?.present_today ?? "—"} accent="present" />
        <StatCard label="Absent now" value={summary?.absent_today ?? "—"} accent="absent" />
        <StatCard label="Active sessions" value={activeSessions} accent="accent" />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Teachers enrolled" value={teachers.length} />
        <StatCard label="Teachers present" value={teachersPresent} accent="present" />
        <StatCard label="Teachers absent" value={teachersAbsent} accent="absent" />
      </div>

      <div className="rounded-xl border border-border bg-bg-elevated">
        <div className="border-b border-border px-5 py-3">
          <h2 className="text-base font-semibold">Today's sessions</h2>
        </div>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wider text-text-muted">
              <th className="px-5 py-3 font-medium">Session</th>
              <th className="px-5 py-3 font-medium">Time</th>
              <th className="px-5 py-3 font-medium">Room</th>
              <th className="px-5 py-3 font-medium">Present / Total</th>
              <th className="px-5 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <TableLoading colSpan={5} />
            ) : schedules.length === 0 ? (
              <TableEmpty colSpan={5} message="No sessions scheduled." />
            ) : (
              schedules.map((session) => {
                const total = summary?.total_students ?? 0;
                const present = presentBySchedule[session.id] ?? 0;
                const ratio = total > 0 ? present / total : 0;
                const isDone = timeStringToMinutes(session.end_time) < now;
                return (
                  <tr key={session.id} className="border-b border-border last:border-0">
                    <td className="px-5 py-3 font-medium">{session.name}</td>
                    <td className="px-5 py-3 font-data text-text-muted">
                      {formatTime(session.start_time)}–{formatTime(session.end_time)}
                    </td>
                    <td className="px-5 py-3 text-text-muted">{session.room}</td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-24 overflow-hidden rounded-full bg-bg-inset">
                          <div
                            className="h-full rounded-full bg-accent"
                            style={{ width: `${Math.min(ratio, 1) * 100}%` }}
                          />
                        </div>
                        <span className="font-data text-xs text-text-muted">
                          {present}/{total}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-data font-medium ${
                          isDone
                            ? "border-border bg-bg-inset text-text-muted"
                            : "border-accent/30 bg-accent-soft text-accent"
                        }`}
                      >
                        {isDone ? "DONE" : "CHECKING"}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
