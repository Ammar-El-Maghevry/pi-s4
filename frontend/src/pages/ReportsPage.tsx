import { useEffect, useMemo, useState } from "react";
import { listAttendanceResults } from "../api/attendance";
import { listStudents } from "../api/students";
import { listTeachers } from "../api/teachers";
import { StatusPill } from "../components/StatusPill";
import { TableEmpty, TableLoading } from "../components/TableStates";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { apiErrorMessage } from "../lib/api";
import { formatTimeOnly } from "../lib/time";
import { AttendanceStatus, type AttendanceResult, type Student, type Teacher } from "../lib/types";

type Person = {
  key: string;
  kind: "student" | "teacher";
  full_name: string;
  identifier: string;
  email: string | null;
  department: string | null;
  studentId?: number;
};

export function ReportsPage() {
  const { user } = useAuth();
  const { showError } = useToast();
  const [students, setStudents] = useState<Student[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [results, setResults] = useState<AttendanceResult[]>([]);
  const [search, setSearch] = useState("");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isSelfView = user?.role !== "admin";

  useEffect(() => {
    async function load() {
      try {
        const [studentData, teacherData, resultData] = await Promise.all([
          listStudents(),
          listTeachers(),
          listAttendanceResults(),
        ]);
        setStudents(studentData);
        setTeachers(teacherData);
        setResults(resultData);
      } catch (err) {
        showError(apiErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const directory: Person[] = useMemo(
    () => [
      ...students.map((s) => ({
        key: `student-${s.id}`,
        kind: "student" as const,
        full_name: s.full_name,
        identifier: s.student_id,
        email: s.email,
        department: s.department,
        studentId: s.id,
      })),
      ...teachers.map((t) => ({
        key: `teacher-${t.id}`,
        kind: "teacher" as const,
        full_name: t.full_name,
        identifier: `T-${t.id}`,
        email: t.email,
        department: null,
      })),
    ],
    [students, teachers],
  );

  const visibleDirectory = useMemo(() => {
    if (isSelfView) {
      return directory.filter((p) => p.email === user?.email);
    }
    if (!search) return directory;
    const q = search.toLowerCase();
    return directory.filter(
      (p) =>
        p.full_name.toLowerCase().includes(q) ||
        p.identifier.toLowerCase().includes(q) ||
        (p.department ?? "").toLowerCase().includes(q),
    );
  }, [directory, isSelfView, search, user?.email]);

  const selected =
    visibleDirectory.find((p) => p.key === selectedKey) ??
    (isSelfView ? visibleDirectory[0] : undefined);

  const personResults = useMemo(
    () => (selected?.studentId ? results.filter((r) => r.student_id === selected.studentId) : []),
    [results, selected],
  );

  const counts = useMemo(
    () => ({
      present: personResults.filter((r) => r.status === AttendanceStatus.PRESENT).length,
      late: personResults.filter((r) => r.status === AttendanceStatus.LATE).length,
      absent: personResults.filter((r) => r.status === AttendanceStatus.ABSENT).length,
    }),
    [personResults],
  );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Reports</h1>
        <p className="text-sm text-text-muted">
          {isSelfView ? "Your attendance history" : "Directory and attendance history"}
        </p>
      </div>

      <div className="flex gap-6">
        {!isSelfView && (
          <div className="w-72 shrink-0 rounded-xl border border-border bg-bg-elevated">
            <div className="border-b border-border p-3">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search people…"
                className="w-full rounded-lg border border-border bg-bg-inset px-3 py-2 text-sm outline-none focus:border-accent"
              />
            </div>
            <div className="max-h-[32rem] overflow-y-auto">
              {isLoading ? (
                <p className="p-4 text-sm text-text-muted">Loading…</p>
              ) : visibleDirectory.length === 0 ? (
                <p className="p-4 text-sm text-text-muted">No matches.</p>
              ) : (
                visibleDirectory.map((p) => (
                  <button
                    key={p.key}
                    onClick={() => setSelectedKey(p.key)}
                    className={`flex w-full flex-col items-start gap-0.5 border-b border-border px-4 py-3 text-left last:border-0 ${
                      selected?.key === p.key ? "bg-accent-soft" : "hover:bg-bg-inset"
                    }`}
                  >
                    <span className="text-sm font-medium">{p.full_name}</span>
                    <span className="font-data text-xs text-text-muted">
                      {p.identifier} · {p.kind}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        )}

        <div className="flex-1">
          {!selected ? (
            <div className="rounded-xl border border-border bg-bg-elevated p-10 text-center text-sm text-text-muted">
              Select a person to view their report.
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="rounded-xl border border-border bg-bg-elevated p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">{selected.full_name}</h2>
                    <p className="font-data text-sm text-text-muted">
                      {selected.identifier} · {selected.kind} · {selected.department ?? "—"}
                    </p>
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-3">
                  <div className="rounded-lg border border-present/30 bg-present/10 p-3 text-center">
                    <div className="font-data text-xl font-semibold text-present">
                      {counts.present}
                    </div>
                    <div className="text-xs text-text-muted">Present</div>
                  </div>
                  <div className="rounded-lg border border-late/30 bg-late/10 p-3 text-center">
                    <div className="font-data text-xl font-semibold text-late">{counts.late}</div>
                    <div className="text-xs text-text-muted">Late</div>
                  </div>
                  <div className="rounded-lg border border-absent/30 bg-absent/10 p-3 text-center">
                    <div className="font-data text-xl font-semibold text-absent">
                      {counts.absent}
                    </div>
                    <div className="text-xs text-text-muted">Absent</div>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-border bg-bg-elevated">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-border text-xs uppercase tracking-wider text-text-muted">
                      <th className="px-5 py-3 font-medium">Date</th>
                      <th className="px-5 py-3 font-medium">Entry</th>
                      <th className="px-5 py-3 font-medium">Exit</th>
                      <th className="px-5 py-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {isLoading ? (
                      <TableLoading colSpan={4} />
                    ) : selected.kind === "teacher" ? (
                      <TableEmpty colSpan={4} message="Attendance tracking applies to students only." />
                    ) : personResults.length === 0 ? (
                      <TableEmpty colSpan={4} />
                    ) : (
                      personResults.map((r) => (
                        <tr key={r.id} className="border-b border-border last:border-0">
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
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
