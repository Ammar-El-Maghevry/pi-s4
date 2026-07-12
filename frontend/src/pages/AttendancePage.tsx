import { useEffect, useMemo, useState } from "react";
import { listAttendanceResults } from "../api/attendance";
import { listClassPlans } from "../api/schedules";
import { listStudents } from "../api/students";
import { listTeacherAttendance, listTeachers } from "../api/teachers";
import { StatusPill } from "../components/StatusPill";
import { TableEmpty, TableLoading } from "../components/TableStates";
import { useLanguage } from "../context/LanguageContext";
import { useToast } from "../context/ToastContext";
import { apiErrorMessage } from "../lib/api";
import { formatTimeOnly, todayIso } from "../lib/time";
import type {
  AttendanceResult,
  ScheduleWithExtras,
  Student,
  Teacher,
  TeacherAttendanceRecord,
} from "../lib/types";
import { AttendanceStatus } from "../lib/types";

type FilterChip = "ALL" | AttendanceStatus;

const CHIPS: FilterChip[] = ["ALL", AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.ABSENT];

export function AttendancePage() {
  const { showError } = useToast();
  const { t } = useLanguage();
  const [results, setResults] = useState<AttendanceResult[]>([]);
  const [students, setStudents] = useState<Record<number, Student>>({});
  const [schedules, setSchedules] = useState<Record<number, ScheduleWithExtras>>({});
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [teacherAttendance, setTeacherAttendance] = useState<TeacherAttendanceRecord[]>([]);
  const [filter, setFilter] = useState<FilterChip>("ALL");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [resultData, studentData, scheduleData, teacherData, teacherAttendanceData] =
          await Promise.all([
            listAttendanceResults(),
            listStudents(),
            listClassPlans(),
            listTeachers(),
            listTeacherAttendance(todayIso()),
          ]);
        setResults(resultData);
        setStudents(Object.fromEntries(studentData.map((s) => [s.id, s])));
        setSchedules(Object.fromEntries(scheduleData.map((s) => [s.id, s])));
        setTeachers(teacherData);
        setTeacherAttendance(teacherAttendanceData);
      } catch (err) {
        showError(apiErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const teacherAttendanceByTeacher = useMemo(
    () => Object.fromEntries(teacherAttendance.map((row) => [row.teacher_id, row])),
    [teacherAttendance],
  );

  const filtered = useMemo(
    () => (filter === "ALL" ? results : results.filter((r) => r.status === filter)),
    [results, filter],
  );

  function chipLabel(chip: FilterChip): string {
    if (chip === "ALL") return t.attendance.chipAll;
    if (chip === AttendanceStatus.PRESENT) return t.statusPill.present;
    if (chip === AttendanceStatus.LATE) return t.statusPill.late;
    return t.statusPill.absent;
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">{t.attendance.title}</h1>
        <p className="text-sm text-text-muted">{t.attendance.subtitle}</p>
      </div>

      <div className="flex gap-1 rounded-lg border border-border bg-bg-elevated p-1 w-fit">
        {CHIPS.map((chip) => (
          <button
            key={chip}
            onClick={() => setFilter(chip)}
            className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
              filter === chip ? "bg-accent-soft text-accent" : "text-text-muted hover:text-text"
            }`}
          >
            {chipLabel(chip)}
          </button>
        ))}
      </div>

      <div className="rounded-xl border border-border bg-bg-elevated">
        <div className="border-b border-border px-5 py-3">
          <h2 className="text-base font-semibold">{t.attendance.studentsSectionTitle}</h2>
        </div>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wider text-text-muted">
              <th className="px-5 py-3 font-medium">{t.attendance.colStudent}</th>
              <th className="px-5 py-3 font-medium">{t.attendance.colClass}</th>
              <th className="px-5 py-3 font-medium">{t.attendance.colDate}</th>
              <th className="px-5 py-3 font-medium">{t.attendance.colEntry}</th>
              <th className="px-5 py-3 font-medium">{t.attendance.colExit}</th>
              <th className="px-5 py-3 font-medium">{t.attendance.colStatus}</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <TableLoading colSpan={6} />
            ) : filtered.length === 0 ? (
              <TableEmpty colSpan={6} />
            ) : (
              filtered.map((r) => (
                <tr key={r.id} className="border-b border-border last:border-0">
                  <td className="px-5 py-3 font-medium">
                    {students[r.student_id]?.full_name ?? `#${r.student_id}`}
                  </td>
                  <td className="px-5 py-3 text-text-muted">
                    {schedules[r.schedule_id]?.name ?? `#${r.schedule_id}`}
                  </td>
                  <td className="px-5 py-3 font-data text-text-muted">{r.result_date}</td>
                  <td className="px-5 py-3 font-data text-text-muted">
                    {formatTimeOnly(r.entry_time)}
                  </td>
                  <td className="px-5 py-3 font-data text-text-muted">
                    {formatTimeOnly(r.exit_time)}
                  </td>
                  <td className="px-5 py-3">
                    <StatusPill status={r.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="rounded-xl border border-border bg-bg-elevated">
        <div className="border-b border-border px-5 py-3">
          <h2 className="text-base font-semibold">{t.attendance.teachersSectionTitle}</h2>
        </div>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wider text-text-muted">
              <th className="px-5 py-3 font-medium">{t.attendance.colTeacher}</th>
              <th className="px-5 py-3 font-medium">{t.attendance.colStatus}</th>
              <th className="px-5 py-3 font-medium">{t.attendance.colMarkedBy}</th>
              <th className="px-5 py-3 font-medium">{t.attendance.colMarkedAt}</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <TableLoading colSpan={4} />
            ) : teachers.length === 0 ? (
              <TableEmpty colSpan={4} />
            ) : (
              teachers.map((teacher) => {
                const record = teacherAttendanceByTeacher[teacher.id];
                return (
                  <tr key={teacher.id} className="border-b border-border last:border-0">
                    <td className="px-5 py-3 font-medium">{teacher.full_name}</td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-data ${
                          record?.is_present
                            ? "border-present/30 bg-present/10 text-present"
                            : "border-absent/30 bg-absent/10 text-absent"
                        }`}
                      >
                        {record?.is_present ? t.attendance.statusPresent : t.attendance.statusAbsent}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-text-muted">
                      {record
                        ? record.source === "camera"
                          ? t.attendance.markedByCamera
                          : t.attendance.markedByManual
                        : "—"}
                    </td>
                    <td className="px-5 py-3 font-data text-text-muted">
                      {formatTimeOnly(record?.marked_at ?? null)}
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
