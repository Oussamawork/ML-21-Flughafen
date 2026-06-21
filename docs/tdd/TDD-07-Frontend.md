# TDD-07 — Web Demo Frontend

**Component:** `frontend/`
**Status:** 🟡 In progress (SkyGuide-identical redesign: landing page + 4-card dashboard; **flight card from `/flight`**, agent chat+mic, map shell, JSON proof; live-verified vs mock backend; production build green)
**Depends on:** TDD-06 (backend API) · **Consumed by:** end users / demo video

---

## 1. Purpose

An interactive web interface to demonstrate the assistant: voice + text input,
chat transcript, and spoken responses — the surface shown in the 7-minute demo
video.

## 2. Requirements satisfied

- *Interactive web interface deployable for any airport.*
- *Voice and/or text interface* (proposal).

## 3. Design

### 3.1 Stack
- **Next.js (React)** + TypeScript + Tailwind. The visual design **replicates the
  teammate's "SkyGuide" prototype** (two screens: a landing page + a 4-card
  dashboard); tokens, layout, and components mirror SkyGuide's `styles.css`,
  re-implemented in Tailwind (palette + `cloudMove`/map CSS in `tailwind.config`/
  `globals.css`).

### 3.2 Core UI
A **landing page** (hero, animated clouds, 6 prep cards) opens into a **ticket-first
dashboard**: the user enters a flight number, the UI loads the flight card + map,
then chats by voice/text. Panels:
- **Ticket strip** — **flight/ticket number input** (typed, validated, never relied
  on from audio — TDD-00), a **Language select** (English / Français / Darija →
  `en`/`fr`/`ary`), and an **"I am here" position selector**. `airport_id` defaults
  to `AUH` (no selector in the strip, matching SkyGuide); the backend stays
  airport-agnostic.
- **Flight Information card** — dark hero (flight no + `dep → arr` route) and a
  label/value grid: airline, terminal, gate, check-in, baggage, boarding, status;
  from `POST /flight`. **Check-in** is KB-sourced (TDD-04) → shows `—` for now;
  **boarding** ← `estimated || scheduled`; status renders as plain text.
- **Airport Map card** — SVG zones + position nodes at seeded `positions` (x,y %),
  current position highlighted; distance/route banner shows the idle state until the
  KB `/map` endpoint lands (TDD-04). Seed transcribed from SkyGuide's
  `airport_map.json` into `lib/map-seed.ts` — **temporary AUH data**, to become
  data-driven per `airport_id`.
- **Airport Agent card** — chat (Passenger/SkyGuide lines) with a **mic button**
  (`MediaRecorder` → 16 kHz WAV → `/converse` → fine-tuned Whisper), typed
  `/chat`, a voice-over toggle + replay (`/speak`), and per-message RTL.
- **Structured API Output card** — pretty-printed last response ("API proof").

> **Mic retained on purpose:** SkyGuide is text-only; we keep mic capture so the
> fine-tuned Whisper (the project's graded ML contribution) stays demoed.

> The frontend **never calls AirLabs directly** — all flight data flows
> frontend → FastAPI → AirLabs (the API key is server-side; TDD-03/06).

### 3.3 Interaction modes
1. **Simple:** REST — record → `/converse` → render text + play audio.
2. **Real-time:** WebSocket `/ws/{session_id}` — streamed partial transcript +
   answer. (v2 once REST path works.)

### 3.4 i18n / RTL
- Chrome is English (matching SkyGuide); the **Language select** controls the
  *assistant's* reply language (`en`/`fr`/`ary`). Agent messages render **RTL** for
  Arabic/Darija replies (`isRtl()` on the detected language), LTR otherwise.

## 4. Interfaces & data contracts

- Consumes TDD-06 endpoints: `/flight`, `/map`, `/chat`, `/converse`, `/speak`,
  `/airports`. Env: `NEXT_PUBLIC_API_BASE_URL`.
- Audio upload: re-encoded to **16 kHz mono WAV in-browser** before `multipart`
  upload (the backend's decoder can't read `MediaRecorder`'s webm/opus).

## 5. Dependencies

`next`, `react`, `typescript`, `tailwindcss`; browser `MediaRecorder` + `Audio`.

## 6. Open questions / risks

- ~~**Browser audio format** (webm/opus) vs Whisper input~~ → **resolved:** the
  frontend re-encodes to 16 kHz mono WAV in-browser (no server ffmpeg needed).
- **Mic permissions / HTTPS** required for `getUserMedia` (works on localhost +
  deployed HTTPS).
- **Latency UX** — show a "thinking/listening" state; stream when WS lands.

## 7. Task checklist

- [x] Next.js app scaffold + typed API client + env config
- [x] Mic capture + `/converse` integration + audio auto-play
- [x] In-browser webm→16 kHz WAV re-encode for voice upload
- [x] Production build green (`next build`, typecheck clean)
- [x] **SkyGuide-identical redesign** — Tailwind tokens + Inter + map/cloud CSS
- [x] **Landing page** — hero + animated clouds + 6 prep cards + "Enter" nav
- [x] **Ticket strip** — flight-number input (typed/validated) · Language ·
      "I am here" position selector · Load flight
- [x] **Flight Information card** (`POST /flight`) — dark hero + label/value grid
      (airline/terminal/gate/check-in/baggage/boarding/status); live-verified vs the
      mock provider (SV624/EK201 + 404 path)
- [x] **Airport Agent card** — chat + mic (`/converse`) + `/chat` + voice-over
      toggle/replay (`/speak`) + per-message RTL
- [x] **Airport Map card** — zones + position nodes from the AUH seed
      (`lib/map-seed.ts`); current position highlighted
- [x] **Structured API Output card** (API proof — last payload)
- [ ] **Live map route** — distance/walk banner + clickable re-route, from `/map` (TDD-04)
- [ ] Wire the agent card to the real LangGraph agent once TDD-02 lands
- [ ] (v2) WebSocket streaming mode
- [ ] Polish for the demo video once real agent/TTS are wired
