# TDD-07 — Web Demo Frontend

**Component:** `frontend/`
**Status:** ⚪ Not started
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
- **Next.js (React)** + TypeScript. Tailwind for styling. Minimal, single-page
  chat experience.

### 3.2 Core UI
- **Chat panel** — message bubbles (user/assistant), shows detected language tag.
- **Mic button** — records via `MediaRecorder` (WebAudio), sends audio to
  `/transcribe` or the `/converse` / WS pipeline.
- **Text input** — fallback typing.
- **Audio playback** — auto-plays the TTS response (`audio_url`).
- **Airport selector** — dropdown bound to `/airports` (proves airport-agnostic;
  defaults to AUH).
- **Tool trace (debug)** — collapsible panel showing which tools fired (great for
  the demo/eval narrative).

### 3.3 Interaction modes
1. **Simple:** REST — record → `/converse` → render text + play audio.
2. **Real-time:** WebSocket `/ws/{session_id}` — streamed partial transcript +
   answer. (v2 once REST path works.)

### 3.4 i18n / RTL
- UI supports **RTL layout** for Arabic/Darija and LTR for French/English; switch
  based on response language. Labels localized (ar/fr/en).

## 4. Interfaces & data contracts

- Consumes TDD-06 endpoints. Env: `NEXT_PUBLIC_API_BASE_URL`.
- Audio upload: `multipart/form-data` (webm/ogg from `MediaRecorder`, transcoded
  server-side if needed).

## 5. Dependencies

`next`, `react`, `typescript`, `tailwindcss`; browser `MediaRecorder` + `Audio`.

## 6. Open questions / risks

- **Browser audio format** (webm/opus) vs Whisper input → transcode server-side
  (ffmpeg) or in `librosa`.
- **Mic permissions / HTTPS** required for `getUserMedia` (works on localhost +
  deployed HTTPS).
- **Latency UX** — show a "thinking/listening" state; stream when WS lands.

## 7. Task checklist

- [ ] Next.js app scaffold + API client + env config
- [ ] Chat panel + text input
- [ ] Mic capture + `/converse` integration + audio playback
- [ ] Airport selector (`/airports`)
- [ ] RTL/LTR + i18n labels
- [ ] Tool-trace debug panel
- [ ] (v2) WebSocket streaming mode
