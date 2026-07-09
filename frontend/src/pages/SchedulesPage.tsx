import { useEffect, useState, type FormEvent } from "react";
import { listCameras } from "../api/cameras";
import {
  assignScheduleCamera,
  assignScheduleClass,
  createClassPlan,
  deleteClassPlan,
  listClassPlans,
  type ClassPlanInput,
} from "../api/schedules";
import { listStudents } from "../api/students";
import { Modal } from "../components/Modal";
import { TableEmpty, TableLoading } from "../components/TableStates";
import { useToast } from "../context/ToastContext";
import { apiErrorMessage } from "../lib/api";
import { formatTime } from "../lib/time";
import type { Camera, ScheduleWithExtras } from "../lib/types";

export function SchedulesPage() {
  const { showError, showSuccess } = useToast();
  const [schedules, setSchedules] = useState<ScheduleWithExtras[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [classOptions, setClassOptions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
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
      showSuccess("Camera assigned");
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
      showSuccess("Class assigned");
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
      showSuccess("Class plan deleted");
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
          <h1 className="text-2xl font-semibold">Class plans</h1>
          <p className="text-sm text-text-muted">
            Weekly session schedule and camera check-in/out windows
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90"
        >
          + New class plan
        </button>
      </div>

      <div className="rounded-xl border border-border bg-bg-elevated">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wider text-text-muted">
              <th className="px-5 py-3 font-medium">Session</th>
              <th className="px-5 py-3 font-medium">Teacher</th>
              <th className="px-5 py-3 font-medium">Room</th>
              <th className="px-5 py-3 font-medium">Day</th>
              <th className="px-5 py-3 font-medium">Time</th>
              <th className="px-5 py-3 font-medium">Check windows</th>
              <th className="px-5 py-3 font-medium">Camera</th>
              <th className="px-5 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <TableLoading colSpan={8} />
            ) : schedules.length === 0 ? (
              <TableEmpty colSpan={8} />
            ) : (
              schedules.map((s) => (
                <tr key={s.id} className="border-b border-border last:border-0">
                  <td className="px-5 py-3 font-medium">{s.name}</td>
                  <td className="px-5 py-3 text-text-muted">{s.teacher}</td>
                  <td className="px-5 py-3 text-text-muted">{s.room}</td>
                  <td className="px-5 py-3 text-text-muted">{s.day}</td>
                  <td className="px-5 py-3 font-data text-text-muted">
                    {formatTime(s.start_time)}–{formatTime(s.end_time)}
                  </td>
                  <td className="px-5 py-3 font-data text-xs text-text-muted">
                    +{s.check_in_offset_minutes}m / -{s.check_out_offset_minutes}m
                  </td>
                  <td className="px-5 py-3">
                    {s.isLocalOnly ? (
                      <span className="text-xs text-text-muted" title="Local-only class plans can't have a camera assigned">
                        —
                      </span>
                    ) : (
                      <select
                        value={s.camera_id ?? ""}
                        disabled={savingCameraFor === s.id}
                        onChange={(e) => handleCameraChange(s.id, e.target.value)}
                        className="w-full rounded-lg border border-border bg-bg-inset px-2 py-1.5 text-xs outline-none focus:border-accent disabled:opacity-50"
                      >
                        <option value="">No camera</option>
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
                      {deletingId === s.id ? "Deleting…" : "Delete"}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <p className="border-t border-border px-5 py-2 text-xs text-text-muted">
          Teacher, room, day and check windows are stored locally in this browser — the backend
          schedule model doesn't have these fields yet. The camera assignment is real and shared
          across all admins.
        </p>
      </div>

      {isModalOpen && (
        <NewClassPlanModal
          onClose={() => setIsModalOpen(false)}
          onCreated={() => {
            setIsModalOpen(false);
            showSuccess("Class plan created");
            load();
          }}
        />
      )}
    </div>
  );
}

function NewClassPlanModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const { showError } = useToast();
  const [form, setForm] = useState<ClassPlanInput>({
    name: "",
    teacher: "",
    room: "",
    day: "Monday",
    start_time: "08:00",
    end_time: "09:30",
    check_in_offset_minutes: 15,
    check_out_offset_minutes: 15,
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
    <Modal title="New class plan" onClose={onClose}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <TextField label="Name" value={form.name} onChange={(v) => set("name", v)} required />
        <TextField
          label="Teacher"
          value={form.teacher}
          onChange={(v) => set("teacher", v)}
          required
        />
        <div className="grid grid-cols-2 gap-3">
          <TextField label="Room" value={form.room} onChange={(v) => set("room", v)} required />
          <div>
            <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-text-muted">
              Day
            </label>
            <select
              value={form.day}
              onChange={(e) => set("day", e.target.value)}
              className="w-full rounded-lg border border-border bg-bg-inset px-3 py-2 text-sm outline-none focus:border-accent"
            >
              {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <TextField
            label="Start time"
            type="time"
            value={form.start_time}
            onChange={(v) => set("start_time", v)}
            required
          />
          <TextField
            label="End time"
            type="time"
            value={form.end_time}
            onChange={(v) => set("end_time", v)}
            required
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <TextField
            label="Check-in offset (min after start)"
            type="number"
            value={String(form.check_in_offset_minutes)}
            onChange={(v) => set("check_in_offset_minutes", Number(v))}
          />
          <TextField
            label="Check-out offset (min before end)"
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
          {isSubmitting ? "Saving…" : "Save"}
        </button>
      </form>
    </Modal>
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
