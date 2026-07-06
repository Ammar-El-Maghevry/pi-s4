// Deliberately a separate, bare axios instance — NOT the shared `api` from
// `lib/api.ts`, whose interceptor wipes the token and force-redirects to
// /login on any 401. This page runs in the phone's own browser with no admin
// session, so a stray 401/network hiccup here must not hijack navigation.
import axios from "axios";
import { DEFAULT_API_BASE_URL } from "../lib/api";
import type { PhoneCameraInfo, WebRTCAnswer, WebRTCOffer } from "../lib/types";

const publicApi = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
});

export async function getPhoneCameraInfo(token: string): Promise<PhoneCameraInfo> {
  const { data } = await publicApi.get<PhoneCameraInfo>(`/phone-camera/${token}`);
  return data;
}

export async function sendOffer(token: string, offer: WebRTCOffer): Promise<WebRTCAnswer> {
  const { data } = await publicApi.post<WebRTCAnswer>(`/phone-camera/${token}/offer`, offer);
  return data;
}

export async function stopPhoneCamera(token: string): Promise<void> {
  await publicApi.post(`/phone-camera/${token}/stop`);
}
