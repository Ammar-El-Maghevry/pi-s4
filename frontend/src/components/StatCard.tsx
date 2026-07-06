import type { ReactNode } from "react";

export function StatCard({
  label,
  value,
  accent,
  icon,
}: {
  label: string;
  value: ReactNode;
  accent?: "present" | "absent" | "late" | "accent";
  icon?: ReactNode;
}) {
  const ACCENT_CLASSES: Record<string, string> = {
    present: "text-present",
    absent: "text-absent",
    late: "text-late",
    accent: "text-accent",
  };
  const valueColor = accent ? ACCENT_CLASSES[accent] : "text-text";
  return (
    <div className="rounded-xl border border-border bg-bg-elevated p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-text-muted">
          {label}
        </span>
        {icon && <span className="text-text-muted">{icon}</span>}
      </div>
      <div className={`mt-2 font-data text-3xl font-semibold ${valueColor}`}>{value}</div>
    </div>
  );
}
