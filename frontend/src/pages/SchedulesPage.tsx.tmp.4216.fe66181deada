import { useEffect, useRef, useState, type FormEvent } from "react";
import { listCameras } from "../api/cameras";
import {
  assignScheduleCamera,
  assignScheduleClass,
  createClassPlan,
  deleteClassPlan,
  importClassPlans,
  listClassPlans,
  type ClassPlanInput,
} from "../api/schedules";
import { listStudents } from "../api/students";
import { Modal } from "../components/Modal";
import { TableEmpty, TableLoading } from "../components/TableStates";
import { useLanguage } from "../context/LanguageContext";
import { useToast } from "../context/ToastContext";
import { apiErrorMessage } from "../lib/api";
import { formatTime } from "../lib/time";
import type { Camera, ScheduleImportResult, ScheduleWithExtras } from "../lib/types";
import type { Translations } from "../lib/i18n";

function dayLabel(day: string, t: Translations): string {
  return t.schedules.dayNames[day] ?? day;
}

export function SchedulesPage() {
  const { showError, showSuccess } = useToast();
  const { t } = useLanguage();
  const [schedules, setSchedules] = useState<ScheduleWithExtras[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [classOptions, setClassOptions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [savingCameraFor, setSavingCameraFor] = useState<number | null>(null);
  const [savingClassFor, setSavingClassFor] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  async function load() {
    setIsLoading(true);
    try {
      const [plans, cams, students] = await Promise.all([
        listClassPlans(),
        listCameras(),
        listStudents(),
      ]);
      setSchedules(plans);
      setCameras(cams);
      setClassOptions(
        Array.from(new Set(students.map((s) => s.class_name).filter((c): c is string => !!c))).sort(),
      );
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCameraChange(scheduleId: number, cameraId: string) {
    setSavingCameraFor(scheduleId);
    try {
      await assignScheduleCamera(scheduleId, cameraId ? Number(cameraId) : null);
      showSuccess(t.schedules.toastCameraAssigned);
      await load();
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setSavingCameraFor(null);
    }
  }

  async function handleClassChange(scheduleId: number, className: string) {
    setSavingClassFor(scheduleId);
    try {
      await assignScheduleClass(scheduleId, className || null);
      showSuccess(t.schedules.toastClassAssigned);
      await load();
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setSavingClassFor(null);
    }
  }

  async function handleDelete(schedule: ScheduleWithExtras) {
    setDeletingId(schedule.id);
    try {
      await deleteClassPlan(schedule.id);
      showSuccess(t.schedules.toastPlanDeleted);
      await load();
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t.schedules.title}</h1>
          <p className="text-sm text-text-muted">{t.schedules.subtitle}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-bg-inset"
          >
            {t.common.import}
          </button>
          <button
            onClick={() => setIsModalOpen(true)}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90"
          >
            {t.schedules.newPlanBtn}
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-bg-elevated">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wider text-text-muted">
              <th className="px-5 py-3 font-medium">{t.schedules.colSession}</th>
              <th className="px-5 py-3 font-medium">{t.schedules.colTeacher}</th>
              <th className="px-5 py-3 font-medium">{t.schedules.colClass}</th>
              <th className="px-5 py-3 font-medium">{t.schedules.colRoom}</th>
              <th className="px-5 py-3 font-medium">{t.schedules.colDay}</th>
              <th className="px-5 py-3 font-medium">{t.schedules.colTime}</th>
              <th className="px-5 py-3 font-medium">{t.schedules.colCheckWindows}</th>
              <th className="px-5 py-3 font-medium">{t.schedules.colCamera}</th>
              <th className="px-5 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <TableLoading colSpan={9} />
            ) : schedules.length === 0 ? (
              <TableEmpty colSpan={9} />
            ) : (
              schedules.map((s) => (
                <tr key={s.id} className="border-b border-border last:border-0">
                  <td className="px-5 py-3 font-medium">{s.name}</td>
                  <td className="px-5 py-3 text-text-muted">{s.teacher}</td>
                  <td className="px-5 py-3">
                    {s.isLocalOnly ? (
                      <span className="text-xs text-text-muted" title={t.schedules.localOnlyClassTitle}>
                        —
                      </span>
                    ) : (
                      <select
                        value={s.class_name ?? ""}
                        disabled={savingClassFor === s.id}
                        onChange={(e) => handleClassChange(s.id, e.target.value)}
                        className="w-full rounded-lg border border-border bg-bg-inset px-2 py-1.5 text-xs outline-none focus:border-accent disabled:opacity-50"
                      >
                        <option value="">{t.common.unassigned}</option>
                        {classOptions.map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td className="px-5 py-3 text-text-muted">{s.room}</td>
                  <td className="px-5 py-3 text-text-muted">{dayLabel(s.day, t)}</td>
                  <td className="px-5 py-3 font-data text-text-muted">
                    {formatTime(s.start_time)}–{formatTime(s.end_time)}
                  </td>
                  <td className="px-5 py-3 font-data text-xs text-text-muted">
                    +{s.check_in_offset_minutes}m / -{s.check_out_offset_minutes}m
                  </td>
                  <td className="px-5 py-3">
                    {s.isLocalOnly ? (
                      <span className="text-xs text-text-muted" title={t.schedules.localOnlyCameraTitle}>
                        —
                      </span>
                    ) : (
                      <select
                        value={s.camera_id ?? ""}
                        disabled={savingCameraFor === s.id}
                        onChange={(e) => handleCameraChange(s.id, e.target.value)}
                        className="w-full rounded-lg border border-border bg-bg-inset px-2 py-1.5 text-xs outline-none focus:border-accent disabled:opacity-50"
                      >
                        <option value="">{t.schedules.noCameraOption}</option>
                        {cameras.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                            {c.location ? ` — ${c.location}` : ""}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => handleDelete(s)}
                      disabled={deletingId === s.id}
                      className="rounded-lg px-2 py-1 text-xs text-red-400 hover:bg-red-500/10 disabled:opacity-50"
                    >
                      {deletingId === s.id ? t.schedules.deleting : t.common.delete}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <p className="border-t border-border px-5 py-2 text-xs text-text-muted">{t.schedules.footnote}</p>
      </div>

      {isModalOpen && (
        <NewClassPlanModal
          classOptions={classOptions}
          onClose={() => setIsModalOpen(false)}
          onCreated={() => {
            setIsModalOpen(false);
            showSuccess(t.schedules.toastPlanCreated);
            load();
          }}
        />
      )}

      {isImportModalOpen && (
        <ImportSchedulesModal
          onClose={() => setIsImportModalOpen(false)}
          onImported={() => load()}
        />
      )}
    </div>
  );
}

function NewClassPlanModal({
  classOptions,
  onClose,
  onCreated,
}: {
  classOptions: string[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const { showError } = useToast();
  const { t } = useLanguage();
  const [form, setForm] = useState<ClassPlanInput>({
    name: "",
    teacher: "",
    room: "",
    day: "Monday",
    start_time: "08:00",
    end_time: "09:30",
    check_in_offset_minutes: 15,
    check_out_offset_minutes: 15,
    class_name: null,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await createClassPlan(form);
      onCreated();
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  function set<K extends keyof ClassPlanInput>(key: K, value: ClassPlanInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  return (
    <Modal title={t.schedules.newPlanModalTitle} onClose={onClose}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <TextField label={t.schedules.fieldName} value={form.name} onChange={(v) => set("name", v)} required />
        <TextField
          label={t.schedules.fieldTeacher}
          value={form.teacher}
          onChange={(v) => set("teacher", v)}
          required
        />
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-text-muted">
            {t.schedules.colClass}
          </label>
          <select
            value={form.class_name ?? ""}
            onChange={(e) => set("class_name", e.target.value || null)}
            className="w-full rounded-lg border border-border bg-bg-inset px-3 py-2 text-sm outline-none focus:border-accent"
          >
            <option value="">{t.common.unassigned}</option>
            {classOptions.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <TextField label={t.schedules.fieldRoom} value={form.room} onChange={(v) => set("room", v)} required />
          <div>
            <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-text-muted">
              {t.schedules.fieldDay}
            </label>
            <select
              value={form.day}
              onChange={(e) => set("day", e.target.value)}
              className="w-full rounded-lg border border-border bg-bg-inset px-3 py-2 text-sm outline-none focus:border-accent"
            >
              {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].map((d) => (
                <option key={d} value={d}>
                  {dayLabel(d, t)}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <TextField
            label={t.schedules.fieldStart}
            type="time"
            value={form.start_time}
            onChange={(v) => set("start_time", v)}
            required
          />
          <TextField
            label={t.schedules.fieldEnd}
            type="time"
            value={form.end_time}
            onChange={(v) => set("end_time", v)}
            required
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <TextField
            label={t.schedules.fieldCheckIn}
            type="number"
            value={String(form.check_in_offset_minutes)}
            onChange={(v) => set("check_in_offset_minutes", Number(v))}
          />
          <TextField
            label={t.schedules.fieldCheckOut}
            type="number"
            value={String(form.check_out_offset_minutes)}
            onChange={(v) => set("check_out_offset_minutes", Number(v))}
          />
        </div>
        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90 disabled:opacity-50"
        >
          {isSubmitting ? t.common.saving : t.common.save}
        </button>
      </form>
    </Modal>
  );
}

function ImportSchedulesModal({
  onClose,
  onImported,
}: {
  onClose: () => void;
  onImported: () => void;
}) {
  const { showError, showSuccess } = useToast();
  const { t } = useLanguage();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScheduleImportResult | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const data = await importClassPlans(file);
      setResult(data);
      onImported();
      if (data.created.length > 0) {
        showSuccess(t.schedules.toastImported({ count: data.created.length }));
      }
      if (data.invalid > 0) {
        showError(t.schedules.toastSkipped({ count: data.invalid }));
      }
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title={t.schedules.importModalTitle} onClose={onClose}>
      {!result ? (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <p className="text-sm text-text-muted">
            {t.schedules.importHelpIntro}
            <code>name</code>, <code>teacher</code>, <code>room</code>, <code>day</code>,{" "}
            <code>start_time</code>, <code>end_time</code>
            {t.schedules.importHelpOutro}
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.pdf"
            required
            className="w-full rounded-lg border border-border bg-bg-inset px-3 py-2 text-sm outline-none file:mr-3 file:rounded-md file:border-0 file:bg-accent-soft file:px-3 file:py-1.5 file:text-accent"
          />
          {error && <p className="text-sm text-absent">{error}</p>}
          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90 disabled:opacity-50"
          >
            {isSubmitting ? t.common.importing : t.common.import}
          </button>
        </form>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <Stat label={t.schedules.importStatCreated} value={result.created.length} />
            <Stat label={t.schedules.importStatSkipped} value={result.invalid} />
          </div>

          {result.created.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wider text-text-muted">
                {t.schedules.importCreatedHeader}
              </p>
              <ul className="max-h-48 overflow-y-auto rounded-lg border border-border text-sm">
                {result.created.map((s) => (
                  <li key={s.schedule_id} className="border-b border-border px-3 py-2 last:border-0">
                    <span className="font-medium">{s.name}</span>{" "}
                    <span className="text-text-muted">
                      — {dayLabel(s.day, t)} {s.start_time}–{s.end_time} · {s.teacher} · {s.room}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.errors.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wider text-text-muted">
                {t.schedules.importSkippedRows}
              </p>
              <ul className="max-h-32 overflow-y-auto rounded-lg border border-border text-xs">
                {result.errors.map((e) => (
                  <li key={e.row} className="border-b border-border px-3 py-1.5 last:border-0">
                    {t.common.rowError({ row: e.row, reason: e.reason })}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={onClose}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-bg-inset"
          >
            {t.common.done}
          </button>
        </div>
      )}
    </Modal>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-bg-inset px-3 py-2">
      <div className="font-data text-lg font-semibold">{value}</div>
      <div className="text-xs text-text-muted">{label}</div>
    </div>
  );
}

function TextField({
  label,
  value,
  onChange,
  type = "text",
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-text-muted">
        {label}
      </label>
      <input
        type={type}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-border bg-bg-inset px-3 py-2 text-sm outline-none focus:border-accent"
      />
    </div>
  );
}
