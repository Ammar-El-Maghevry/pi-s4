import { useState } from "react";
import { Modal } from "./Modal";
import { PhotoPicker } from "./PhotoPicker";

export function PhotoCaptureModal({
  title,
  onClose,
  onCapture,
  isSubmitting,
  error,
}: {
  title: string;
  onClose: () => void;
  onCapture: (photo: Blob) => void;
  isSubmitting: boolean;
  error: string | null;
}) {
  const [pending, setPending] = useState<Blob | null>(null);

  return (
    <Modal title={title} onClose={onClose}>
      <div className="flex flex-col gap-3">
        <PhotoPicker value={pending} onChange={setPending} height={320} hideRetakeButton={!!pending} />

        {error && (
          <div className="rounded-lg border border-absent/30 bg-absent/10 px-3 py-2 text-sm text-absent">
            {error}
          </div>
        )}

        {pending && (
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setPending(null)}
              className="rounded-lg border border-border px-4 py-2 text-sm text-text-muted hover:text-text"
            >
              Retake
            </button>
            <button
              onClick={() => onCapture(pending)}
              disabled={isSubmitting}
              className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90 disabled:opacity-50"
            >
              {isSubmitting ? "Uploading…" : "Save photo"}
            </button>
          </div>
        )}
      </div>
    </Modal>
  );
}
