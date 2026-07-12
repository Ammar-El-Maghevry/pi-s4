import { useLanguage } from "../context/LanguageContext";
import { AttendanceStatus } from "../lib/types";

const STYLES: Record<AttendanceStatus, string> = {
  [AttendanceStatus.PRESENT]: "bg-present/10 text-present border-present/30",
  [AttendanceStatus.LATE]: "bg-late/10 text-late border-late/30",
  [AttendanceStatus.ABSENT]: "bg-absent/10 text-absent border-absent/30",
};

export function StatusPill({ status }: { status: AttendanceStatus }) {
  const { t } = useLanguage();
  const LABELS: Record<AttendanceStatus, string> = {
    [AttendanceStatus.PRESENT]: t.statusPill.present,
    [AttendanceStatus.LATE]: t.statusPill.late,
    [AttendanceStatus.ABSENT]: t.statusPill.absent,
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium font-data ${STYLES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
