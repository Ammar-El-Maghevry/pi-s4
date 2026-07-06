import { useEffect, useRef, useState } from "react";
import { Modal } from "./Modal";

type Mode = "upload" | "camera";

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
  const [mode, setMode] = useState<Mode>("upload");
  const [preview, setPreview] = useState<string | null>(null);
  const [pendingBlob, setPendingBlob] = useState<Blob | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (mode !== "camera") {
      stopStream();
      return;
    }
    navigator.mediaDevices
      .getUserMedia({ video: { width: 640, height: 480 } })
      .then((stream) => {
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch((err) => setCameraError(err.message ?? "Could not access the camera"));
    return stopStream;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

  function stopStream() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setPendingBlob(file);
    setPreview(URL.createObjectURL(file));
  }

  function handleCaptureFrame() {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) return;
      setPendingBlob(blob);
      setPreview(URL.createObjectURL(blob));
    }, "image/jpeg");
  }

  function handleConfirm() {
    if (pendingBlob) onCapture(pendingBlob);
  }

  function retake() {
    setPreview(null);
    setPendingBlob(null);
  }

  return (
    <Modal title={title} onClose={onClose}>
      <div className="flex flex-col gap-3">
        <div className="flex gap-1 rounded-lg border border-border bg-bg-inset p-1 w-fit">
          <button
            onClick={() => {
              retake();
              setMode("upload");
            }}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${mode === "upload" ? "bg-accent-soft text-accent" : "text-text-muted"}`}
          >
            Upload file
          </button>
          <button
            onClick={() => {
              retake();
              setMode("camera");
            }}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${mode === "camera" ? "bg-accent-soft text-accent" : "text-text-muted"}`}
          >
            Use camera
          </button>
        </div>

        <div className="flex items-center justify-center overflow-hidden rounded-lg border border-border bg-bg-inset" style={{ height: 320 }}>
          {preview ? (
            <img src={preview} alt="Captured" className="h-full w-full object-contain" />
          ) : mode === "upload" ? (
            <label className="flex cursor-pointer flex-col items-center gap-2 text-sm text-text-muted">
              <span>Click to choose an image (JPEG/PNG/WebP)</span>
              <input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={handleFileChange} />
            </label>
          ) : cameraError ? (
            <span className="px-4 text-center text-sm text-absent">{cameraError}</span>
          ) : (
            // eslint-disable-next-line jsx-a11y/media-has-caption
            <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-contain" />
          )}
        </div>

        {error && (
          <div className="rounded-lg border border-absent/30 bg-absent/10 px-3 py-2 text-sm text-absent">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2">
          {preview ? (
            <>
              <button
                onClick={retake}
                className="rounded-lg border border-border px-4 py-2 text-sm text-text-muted hover:text-text"
              >
                Retake
              </button>
              <button
                onClick={handleConfirm}
                disabled={isSubmitting}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90 disabled:opacity-50"
              >
                {isSubmitting ? "Uploading…" : "Save photo"}
              </button>
            </>
          ) : mode === "camera" && !cameraError ? (
            <button
              onClick={handleCaptureFrame}
              className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90"
            >
              Capture
            </button>
          ) : null}
        </div>
      </div>
    </Modal>
  );
}
