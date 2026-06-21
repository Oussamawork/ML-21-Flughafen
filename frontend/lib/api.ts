// Typed client for the wayfinding backend (TDD-06).
import { toWav16kMono } from "./audio";
import type {
  AirportsResponse,
  ChatResponse,
  ConverseResponse,
  FlightResponse,
  Language,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

function absolute(url: string): string {
  return url.startsWith("http") ? url : `${API_BASE}${url}`;
}

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return (await res.json()) as T;
}

export async function getAirports(): Promise<AirportsResponse> {
  return asJson(await fetch(`${API_BASE}/airports`));
}

// Lookup kinds the dashboard surfaces differently: not-found vs provider-down.
export type FlightErrorKind = "not_found" | "unavailable" | "error";

export class FlightLookupError extends Error {
  constructor(public kind: FlightErrorKind) {
    super(kind);
  }
}

export async function getFlight(params: {
  flightNumber: string;
  airportId?: string;
  position?: string;
}): Promise<FlightResponse> {
  const res = await fetch(`${API_BASE}/flight`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      flight_number: params.flightNumber,
      airport_id: params.airportId ?? null,
      position: params.position ?? null,
    }),
  });
  if (res.ok) return (await res.json()) as FlightResponse;
  if (res.status === 404) throw new FlightLookupError("not_found");
  if (res.status === 503) throw new FlightLookupError("unavailable");
  throw new FlightLookupError("error");
}

export async function sendChat(params: {
  text: string;
  sessionId?: string;
  airportId?: string;
  language?: Language;
  flightNumber?: string;
  position?: string;
}): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: params.text,
      session_id: params.sessionId ?? null,
      airport_id: params.airportId ?? null,
      language: params.language ?? null,
      flight_number: params.flightNumber ?? null,
      position: params.position ?? null,
    }),
  });
  return asJson(res);
}

export async function converse(params: {
  audio: Blob;
  sessionId?: string;
  filename?: string;
  flightNumber?: string;
  position?: string;
}): Promise<ConverseResponse> {
  // Re-encode to 16 kHz mono WAV; the browser records webm/opus, which the
  // backend's audio decoder cannot read.
  const wav = await toWav16kMono(params.audio);
  const form = new FormData();
  form.append("audio", wav, params.filename ?? "clip.wav");
  if (params.sessionId) form.append("session_id", params.sessionId);
  if (params.flightNumber) form.append("flight_number", params.flightNumber);
  if (params.position) form.append("position", params.position);
  const res = await fetch(`${API_BASE}/converse`, { method: "POST", body: form });
  const data = await asJson<ConverseResponse>(res);
  return { ...data, audio_url: absolute(data.audio_url) };
}

// Fetch synthesized speech for an assistant text reply (text-mode playback).
export async function speak(text: string, language: Language): Promise<string> {
  const res = await fetch(`${API_BASE}/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });
  if (!res.ok) throw new Error(`speak failed: ${res.status}`);
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
