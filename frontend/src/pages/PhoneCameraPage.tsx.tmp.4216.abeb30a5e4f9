import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { getPhoneCameraInfo, sendOffer, stopPhoneCamera } from "../api/phoneCamera";
import { useLanguage } from "../context/LanguageContext";
import { apiErrorMessage } from "../lib/api";
import type { Translations } from "../lib/i18n";
import type { PhoneCameraInfo } from "../lib/types";

type Status =
  | "loading-info"
  | "not-found"
  | "idle"
  | "requesting-camera"
  | "connecting"
  | "connected"
  | "error";

const ICE_GATHERING_TIMEOUT_MS = 5000;

async function waitForIceGatheringComplete(pc: RTCPeerConnection): Promise<void> {
  if (pc.iceGatheringState === "complete") return;
  await new Promise<void>((resolve) => {
    const timer = setTimeout(() => {
      pc.removeEventListener("icegatheringstatechange", check);
      resolve();
    }, ICE_GATHERING_TIMEOUT_MS);
    function check() {
      if (pc.iceGatheringState === "complete") {
        clearTimeout(timer);
        pc.removeEventListener("icegatheringstatechange", check);
        resolve();
      }
    }
    pc.addEventListener("icegatheringstatechange", check);
  });
}

export function PhoneCameraPage() {
  const { token } = useParams<{ token: string }>();
  const { t } = useLanguage();
  const [status, setStatus] = useState<Status>("loading-info");
  const [info, setInfo] = useState<PhoneCameraInfo | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);

  useEffect(() => {
    if (!token) return;
    getPhoneCameraInfo(token)
      .then((data) => {
        setInfo(data);
        setStatus("idle");
      })
      .catch(() => setStatus("not-found"));
  }, [token]);

  useEffect(() => stopEverything, []);

  function stopEverything() {
    pcRef.current?.close();
    pcRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }

  async function handleStart() {
    if (!token) return;
    setErrorMessage(null);
    setStatus("requesting-camera");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;

      setStatus("connecting");
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });
      pcRef.current = pc;
      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      pc.addEventListener("connectionstatechange", () => {
        if (pc.connectionState === "connected") setStatus("connected");
        if (pc.connectionState === "failed" || pc.connectionState === "disconnected") {
          setErrorMessage(t.phoneCamera.connectionLost);
          setStatus("error");
        }
      });

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      await waitForIceGatheringComplete(pc);

      const answer = await sendOffer(token, {
        sdp: pc.localDescription!.sdp,
        type: pc.localDescription!.type,
      });
      await pc.setRemoteDescription(answer as RTCSessionDescriptionInit);
    } catch (err) {
      stopEverything();
      setErrorMessage(err instanceof DOMException ? cameraErrorMessage(err, t) : apiErrorMessage(err));
      setStatus("error");
    }
  }

  async function handleStop() {
    stopEverything();
    setStatus("idle");
    if (token) await stopPhoneCamera(token).catch(() => {});
  }

  return (
    <div className="flex min-h-screen flex-col items-center gap-4 bg-bg p-4 text-text">
      <div className="flex w-full max-w-md flex-col gap-4">
        <h1 className="text-center text-xl font-semibold">{t.phoneCamera.headerTitle}</h1>

        {!window.isSecureContext && (
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-amber-500">
            {t.phoneCamera.httpWarning}
          </div>
        )}

        {status === "loading-info" && <p className="text-center text-text-muted">{t.common.loading}</p>}

        {status === "not-found" && (
          <p className="text-center text-absent">{t.phoneCamera.notFound}</p>
        )}

        {status !== "loading-info" && status !== "not-found" && (
          <>
            <p className="text-center text-text-muted">
              {t.phoneCamera.pairingWith({ name: info?.name ?? "", location: info?.location ?? "" })}
            </p>

            <div className="flex aspect-video items-center justify-center overflow-hidden rounded-lg border border-border bg-bg-inset">
              {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
              <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-contain" />
            </div>

            {errorMessage && (
              <div className="rounded-lg border border-absent/30 bg-absent/10 px-3 py-2 text-sm text-absent">
                {errorMessage}
              </div>
            )}

            <p className="text-center text-sm text-text-muted">{statusLabel(status, t)}</p>

            {status === "connected" ? (
              <button
                onClick={handleStop}
                className="rounded-lg border border-absent/50 px-4 py-2 text-sm font-medium text-absent hover:bg-absent/10"
              >
                {t.phoneCamera.stopBtn}
              </button>
            ) : (
              <button
                onClick={handleStart}
                disabled={status === "requesting-camera" || status === "connecting"}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-black hover:opacity-90 disabled:opacity-50"
              >
                {status === "requesting-camera" || status === "connecting"
                  ? t.phoneCamera.connecting
                  : t.phoneCamera.startBtn}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function statusLabel(status: Status, t: Translations): string {
  switch (status) {
    case "idle":
      return t.phoneCamera.statusIdle;
    case "requesting-camera":
      return t.phoneCamera.statusRequestingCamera;
    case "connecting":
      return t.phoneCamera.statusConnecting;
    case "connected":
      return t.phoneCamera.statusConnected;
    case "error":
      return t.phoneCamera.statusError;
    default:
      return "";
  }
}

function cameraErrorMessage(err: DOMException, t: Translations): string {
  if (err.name === "NotAllowedError") return t.phoneCamera.errNotAllowed;
  if (err.name === "NotFoundError") return t.phoneCamera.errNotFound;
  return err.message || t.phoneCamera.errGeneric;
}
