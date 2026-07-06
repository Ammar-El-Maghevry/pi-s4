import { AttendanceStatus } from "../lib/types";

const STYLES: Record<AttendanceStatus, string> = {
  [AttendanceStatus.PRESENT]: "bg-present/10 text-present border-present/30",
  [AttendanceStatus.LATE]: "bg-late/10 text-late border-late/30",
  [AttendanceStatus.ABSENT]: "bg-absent/10 text-absent border-absent/30",
};

const LABELS: Record<AttendanceStatus, string> = {
  [AttendanceStatus.PRESENT]: "Present",
  [AttendanceStatus.LATE]: "Late",
  [AttendanceStatus.ABSENT]: "Absent",
};

export function StatusPill({ status }: { status: AttendanceStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium font-data ${STYLES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
