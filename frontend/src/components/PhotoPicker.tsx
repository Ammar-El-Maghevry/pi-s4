import { useEffect, useRef, useState } from "react";
import { useLanguage } from "../context/LanguageContext";

type Mode = "upload" | "camera";

export function PhotoPicker({
  value,
  onChange,
  height = 240,
  hideRetakeButton = false,
}: {
  value: Blob | null;
  onChange: (photo: Blob | null) => void;
  height?: number;
  // Set when the caller wants to render its own Retake button alongside a
  // Save/Confirm action in one row (see PhotoCaptureModal), instead of
  // PhotoPicker's own Retake sitting alone on its own row.
  hideRetakeButton?: boolean;
}) {
  const { t } = useLanguage();
  const [mode, setMode] = useState<Mode>("upload");
  const [preview, setPreview] = useState<string | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    // Also re-runs when `value` clears (e.g. Retake): the <video> element
    // unmounts while a preview is shown, so the stream must be reattached to
    // the freshly remounted node rather than reused from the old one — and
    // there's no need to keep the camera running while a preview is up.
    if (mode !== "camera" || value) {
      stopStream();
      return;
    }
    let cancelled = false;
    navigator.mediaDevices
      .getUserMedia({ video: { width: 640, height: 480 } })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch((err) => setCameraError(err.message ?? t.photoPicker.cameraAccessError));
    return () => {
      cancelled = true;
      stopStream();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, value]);

  useEffect(() => {
    if (!value) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(value);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [value]);

  function stopStream() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onChange(file);
  }

  function handleCaptureFrame() {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) onChange(blob);
    }, "image/jpeg");
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex w-fit gap-1 rounded-lg border border-border bg-bg-inset p-1">
        <button
          type="button"
          onClick={() => {
            onChange(null);
            setMode("upload");
          }}
          className={`rounded-md px-3 py-1.5 text-sm font-medium ${mode === "upload" ? "bg-accent-soft text-accent" : "text-text-muted"}`}
        >
          {t.photoPicker.uploadFile}
        </button>
        <button
          type="button"
          onClick={() => {
            onChange(null);
            setMode("camera");
          }}
          className={`rounded-md px-3 py-1.5 text-sm font-medium ${mode === "camera" ? "bg-accent-soft text-accent" : "text-text-muted"}`}
        >
          {t.photoPicker.useCamera}
        </button>
      </div>

      <div
        className="flex items-center justify-center overflow-hidden rounded-lg border border-border bg-bg-inset"
        style={{ height }}
      >
        {preview ? (
          <img src={preview} alt="Captured" className="h-full w-full object-contain" />
        ) : mode === "upload" ? (
          <label className="flex cursor-pointer flex-col items-center gap-2 text-sm text-text-muted">
            <span>{t.photoPicker.clickToChoose}</span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>
        ) : cameraError ? (
          <span className="px-4 text-center text-sm text-absent">{cameraError}</span>
        ) : (
          // eslint-disable-next-line jsx-a11y/media-has-caption
          <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-contain" />
        )}
      </div>

      <div className="flex justify-end gap-2">
        {preview ? (
          hideRetakeButton ? null : (
            <button
              type="button"
              onClick={() => onChange(null)}
              className="rounded-lg border border-border px-3 py-1.5 text-sm text-text-muted hover:text-text"
            >
              Retake
            </button>
          )
        ) : mode === "camera" && !cameraError ? (
          <button
            type="button"
            onClick={handleCaptureFrame}
            className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-black hover:opacity-90"
          >
            Capture
          </button>
        ) : null}
      </div>
    </div>
  );
}
