# TDD-07 — Web Demo Frontend

**Component:** `frontend/`
**Status:** 🟡 In progress (Next.js app built; text+voice, RTL, airport selector; production build green)
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
- **Next.js (React)** + TypeScript. Tailwind for styling. **Dashboard layout**
  (chat + context panels), evolving from the v1 single chat column — inspired by
  and surpassing the teammate's "SkyGuide" prototype.

### 3.2 Core UI
A **ticket-first dashboard**: the user enters a flight number, the UI loads the
flight card + map, then chats by voice/text. Panels:
- **Entry bar** — **flight/ticket number input** (typed, validated, never relied on
  from audio — TDD-00), **airport selector** (bound to `/airports`, default `AUH`),
  and **"I am here" position selector** (options from `GET /map`).
- **Flight Information card** — flight no, airline, route, terminal, gate, status,
  times, baggage (arrivals); from `POST /flight` / agent `flight` payload. Fields
  AirLabs lacks (check-in) come from the backend KB; missing fields show gracefully.
- **Airport Map panel** — SVG of map nodes at `positions` (x,y %) with a highlighted
  **route polyline** to the gate and a live distance/walk-time banner; clickable
  nodes re-route. Driven by the agent/`/flight` `route` payload (ported from
  SkyGuide's `renderMap`, but data-driven per `airport_id`).
- **Chat panel** — message bubbles (user/assistant), detected-language tag.
- **Structured-output panel** — pretty-printed last response ("API proof"), with
  the collapsible **tool trace** + per-stage latency.
- **Mic button** — records via `MediaRecorder`, re-encodes to 16 kHz mono WAV
  in-browser, sends to `/converse`. **Text input** — fallback typing.
- **Audio playback** — auto-plays the TTS response (`audio_url`).

> The frontend **never calls AirLabs directly** — all flight data flows
> frontend → FastAPI → AirLabs (the API key is server-side; TDD-03/06).

### 3.3 Interaction modes
1. **Simple:** REST — record → `/converse` → render text + play audio.
2. **Real-time:** WebSocket `/ws/{session_id}` — streamed partial transcript +
   answer. (v2 once REST path works.)

### 3.4 i18n / RTL
- UI supports **RTL layout** for Arabic/Darija and LTR for French/English; switch
  based on response language. Labels localized (ar/fr/en).

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
- [x] Chat panel + text input (`/chat` + `/speak` playback)
- [x] Mic capture + `/converse` integration + audio auto-play
- [x] Airport selector (`/airports`)
- [x] RTL/LTR + i18n labels (en/fr/ar)
- [x] Tool-trace panel + per-stage latency display
- [x] Production build green (`next build`, typecheck clean)
- [x] In-browser webm→16 kHz WAV re-encode for voice upload
- [ ] **Dashboard layout** (chat + flight card + map + structured panel)
- [ ] **Flight-number input** + **position selector** (from `/map`); `airport_id` default AUH
- [ ] **Flight Information card** (from `/flight` / agent `flight` payload)
- [ ] **Airport Map panel** — SVG route + clickable nodes + distance/walk banner
- [ ] **Structured-output panel** (API proof) + tool trace + latency
- [ ] (v2) WebSocket streaming mode
- [ ] Polish for the demo video once real STT/agent/TTS are wired
