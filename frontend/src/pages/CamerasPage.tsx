import { useEffect, useState, type FormEvent } from "react";
import {
  createCamera,
  deleteCamera,
  listCameras,
  sendPairingEmail,
  testCameraConnection,
  updateCamera,
} from "../api/cameras";
import { Modal } from "../components/Modal";
import { TableEmpty, TableLoading } from "../components/TableStates";
import { useLanguage } from "../context/LanguageContext";
import { useToast } from "../context/ToastContext";
import { apiErrorMessage } from "../lib/api";
import type { Translations } from "../lib/i18n";
import { CameraSourceType, type Camera, type CameraCreate } from "../lib/types";

// The link is computed server-side (from PHONE_PAIRING_BASE_URL) rather than
// from window.location: the admin dashboard is commonly viewed over
// "localhost" or a different LAN alias than the phone can actually reach.
async function copyPairingLink(
  link: string,
  toast: { showSuccess: (msg: string) => void; showError: (msg: string) => void },
  t: Translations,
): Promise<void> {
  try {
    await navigator.clipboard.writeText(link);
    toast.showSuccess(t.cameras.toastPairingLinkCopied);
  } catch {
    toast.showError(link);
  }
}

export function CamerasPage() {
  const { showError, showSuccess } = useToast();
  const { t } = useLanguage();
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState<Camera | null>(null);
  const [testingId, setTestingId] = useState<number | null>(null);
  const [sendingEmailId, setSendingEmailId] = useState<number | null>(null);

  async function load() {
    setIsLoading(true);
    try {
      setCameras(await listCameras());
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleDelete(id: number) {
    if (!confirm(t.cameras.confirmDeleteCamera)) {
      return;
    }
    try {
      await deleteCamera(id);
      showSuccess(t.cameras.toastCameraRemoved);
      load();
    } catch (err) {
      showError(apiErrorMessage(err));
    }
  }

  async function handleTest(id: number) {
    setTestingId(id);
    try {
      const result = await testCameraConnection(id);
      if (result.success) {
        showSuccess(
          result.width && result.height
            ? t.cameras.toastConnectedWithRes({ width: result.width, height: result.height })
            : t.cameras.toastConnected,
        );
      } else {
        showError(result.message);
      }
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setTestingId(null);
    }
  }

  async function handleSendEmail(id: number) {
    setSendingEmailId(id);
    try {
      const result = await sendPairingEmail(id);
      showSuccess(result.message);
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setSendingEmailId(null);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t.cameras.title}</h1>
          <p className="text-sm text-text-muted">{t.cameras.subtitle}</p>
        </div>
        <button
          onClick={() => {
            setEditing(null);
            setIsModalOpen(true);
          }}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90"
        >
          {t.cameras.addCameraBtn}
        </button>
      </div>

      <div className="rounded-xl border border-border bg-bg-elevated">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wider text-text-muted">
              <th className="px-5 py-3 font-medium">{t.cameras.colName}</th>
              <th className="px-5 py-3 font-medium">{t.cameras.colLocation}</th>
              <th className="px-5 py-3 font-medium">{t.cameras.colSource}</th>
              <th className="px-5 py-3 font-medium" title={t.cameras.colEnabledTooltip}>
                {t.cameras.colEnabled}
              </th>
              <th className="px-5 py-3" />
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <TableLoading colSpan={5} />
            ) : cameras.length === 0 ? (
              <TableEmpty colSpan={5} />
            ) : (
              cameras.map((c) => (
                <tr key={c.id} className="border-b border-border last:border-0">
                  <td className="px-5 py-3 font-medium">{c.name}</td>
                  <td className="px-5 py-3 text-text-muted">{c.location ?? "—"}</td>
                  <td className="px-5 py-3 font-data text-xs text-text-muted">
                    {c.source_type === CameraSourceType.PHONE ? (
                      <span className="inline-flex items-center rounded-full border border-accent/30 bg-accent-soft px-2.5 py-0.5 font-sans text-accent">
                        {t.cameras.phoneCameraBadge}
                      </span>
                    ) : (
                      c.source_url
                    )}
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-data ${
                        c.is_active
                          ? "border-present/30 bg-present/10 text-present"
                          : "border-border bg-bg-inset text-text-muted"
                      }`}
                    >
                      {c.is_active ? t.cameras.statusEnabled : t.cameras.statusDisabled}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex justify-end gap-3">
                      {c.source_type === CameraSourceType.PHONE && c.pairing_link && (
                        <button
                          onClick={() => copyPairingLink(c.pairing_link!, { showSuccess, showError }, t)}
                          className="text-xs text-text-muted hover:text-accent"
                        >
                          {t.cameras.copyLink}
                        </button>
                      )}
                      {c.source_type === CameraSourceType.PHONE && c.pairing_email && (
                        <button
                          onClick={() => handleSendEmail(c.id)}
                          disabled={sendingEmailId === c.id}
                          className="text-xs text-text-muted hover:text-accent disabled:opacity-50"
                        >
                          {sendingEmailId === c.id ? t.cameras.sendingEmail : t.cameras.sendEmail}
                        </button>
                      )}
                      <button
                        onClick={() => handleTest(c.id)}
                        disabled={testingId === c.id}
                        className="text-xs text-text-muted hover:text-accent disabled:opacity-50"
                      >
                        {testingId === c.id ? t.cameras.testing : t.cameras.testBtn}
                      </button>
                      <button
                        onClick={() => {
                          setEditing(c);
                          setIsModalOpen(true);
                        }}
                        className="text-xs text-text-muted hover:text-text"
                      >
                        {t.common.edit}
                      </button>
                      <button
                        onClick={() => handleDelete(c.id)}
                        className="text-xs text-text-muted hover:text-absent"
                      >
                        {t.common.remove}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {isModalOpen && (
        <CameraModal
          camera={editing}
          onClose={() => setIsModalOpen(false)}
          onSaved={() => {
            setIsModalOpen(false);
            showSuccess(editing ? t.cameras.toastCameraUpdated : t.cameras.toastCameraAdded);
            load();
          }}
        />
      )}
    </div>
  );
}

function CameraModal({
  camera,
  onClose,
  onSaved,
}: {
  camera: Camera | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { showError, showSuccess } = useToast();
  const { t } = useLanguage();
  const [form, setForm] = useState<CameraCreate>({
    name: camera?.name ?? "",
    location: camera?.location ?? "",
    source_type: camera?.source_type ?? CameraSourceType.IP_CAMERA,
    source_url: camera?.source_type === CameraSourceType.PHONE ? "" : (camera?.source_url ?? ""),
    pairing_email: camera?.pairing_email ?? "",
    is_active: camera?.is_active ?? true,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [savedCamera, setSavedCamera] = useState<{
    id: number;
    name: string;
    webrtc_token: string;
    pairing_email: string | null;
    pairing_link: string;
  } | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = {
        ...form,
        location: form.location || null,
        pairing_email: form.pairing_email || null,
      };
      const saved = camera ? await updateCamera(camera.id, payload) : await createCamera(payload);
      if (saved.source_type === CameraSourceType.PHONE && saved.webrtc_token && saved.pairing_link) {
        setSavedCamera({
          id: saved.id,
          name: saved.name,
          webrtc_token: saved.webrtc_token,
          pairing_email: saved.pairing_email,
          pairing_link: saved.pairing_link,
        });
        return;
      }
      onSaved();
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSendEmailNow() {
    if (!savedCamera) return;
    setIsSendingEmail(true);
    try {
      const result = await sendPairingEmail(savedCamera.id);
      showSuccess(result.message);
    } catch (err) {
      showError(apiErrorMessage(err));
    } finally {
      setIsSendingEmail(false);
    }
  }

  function set<K extends keyof CameraCreate>(key: K, value: CameraCreate[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  if (savedCamera) {
    return (
      <Modal title={t.cameras.phoneSavedTitle} onClose={onSaved}>
        <div className="flex flex-col gap-3">
          <p className="text-sm text-text-muted">
            {t.cameras.phoneSavedHintPrefix}
            <span className="font-medium text-text">{savedCamera.name}</span>
            {t.cameras.phoneSavedHintSuffix}
          </p>
          <div className="flex items-center gap-2 rounded-lg border border-border bg-bg-inset px-3 py-2 text-xs font-data">
            <span className="flex-1 truncate">{savedCamera.pairing_link}</span>
            <button
              onClick={() => copyPairingLink(savedCamera.pairing_link, { showSuccess, showError }, t)}
              className="shrink-0 text-accent hover:opacity-80"
            >
              {t.cameras.copyBtn}
            </button>
          </div>
          {savedCamera.pairing_email && (
            <button
              onClick={handleSendEmailNow}
              disabled={isSendingEmail}
              className="self-start rounded-lg border border-border px-3 py-1.5 text-sm text-text-muted hover:text-text disabled:opacity-50"
            >
              {isSendingEmail
                ? t.cameras.sendingEmail
                : t.cameras.emailThisLink({ email: savedCamera.pairing_email })}
            </button>
          )}
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-500">
            {t.cameras.certWarning}
          </div>
          <button
            onClick={onSaved}
            className="mt-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90"
          >
            {t.common.done}
          </button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal title={camera ? t.cameras.modalTitleEdit : t.cameras.modalTitleAdd} onClose={onClose}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-text-muted">
            {t.cameras.sourceLabel}
          </label>
          <div className="flex gap-1 rounded-lg border border-border bg-bg-inset p-1">
            {(
              [
                [CameraSourceType.IP_CAMERA, t.cameras.sourceIpOption],
                [CameraSourceType.PHONE, t.cameras.sourcePhoneOption],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => set("source_type", value)}
                className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  form.source_type === value
                    ? "bg-accent-soft text-accent"
                    : "text-text-muted hover:text-text"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <Field label={t.cameras.fieldName} value={form.name} onChange={(v) => set("name", v)} required />
        <Field
          label={t.cameras.fieldLocation}
          value={form.location ?? ""}
          onChange={(v) => set("location", v)}
        />
        {form.source_type === CameraSourceType.IP_CAMERA ? (
          <Field
            label={t.cameras.fieldSourceUrl}
            value={form.source_url ?? ""}
            onChange={(v) => set("source_url", v)}
            required
          />
        ) : (
          <>
            <p className="rounded-lg border border-border bg-bg-inset px-3 py-2 text-xs text-text-muted">
              {t.cameras.pairingHint}
            </p>
            <Field
              label={t.cameras.fieldPairingEmail}
              value={form.pairing_email ?? ""}
              onChange={(v) => set("pairing_email", v)}
              type="email"
            />
          </>
        )}
        <label className="flex items-center gap-2 text-sm text-text-muted">
          <input
            type="checkbox"
            checked={form.is_active ?? true}
            onChange={(e) => set("is_active", e.target.checked)}
            className="rounded border-border"
          />
          {t.cameras.activeCheckbox}
        </label>
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

function Field({
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
