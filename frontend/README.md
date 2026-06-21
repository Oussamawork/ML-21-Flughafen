# Frontend — Web Demo (TDD-07)

The demo UI for the Smart Airport Wayfinding Assistant: a **ticket-first
dashboard** that talks to the FastAPI backend (TDD-06). Its visual design mirrors
the teammate's "SkyGuide" prototype — a landing page plus a 4-card dashboard.
Design: `../docs/tdd/TDD-07-Frontend.md`.

Next.js (App Router) + React + TypeScript + Tailwind.

## Features

- **Landing page** — hero, animated clouds, and a 6-card "prepare for your journey"
  grid; "Enter flight ticket" opens the dashboard.
- **Ticket strip** — typed flight-number input (structured, never parsed from
  audio), a Language select (English / Français / Darija), and an "I am here"
  position selector.
- **Flight Information card** — dark hero (flight no + route) + a label/value grid
  (airline, terminal, gate, check-in, baggage, boarding, status), from `POST /flight`.
  Check-in is KB-sourced later (TDD-04).
- **Airport Agent card** — text + **mic** (`MediaRecorder` → `POST /converse` →
  fine-tuned Whisper) + typed `POST /chat`; voice-over playback via `POST /speak`,
  with a replay button. Per-message RTL for Arabic/Darija replies.
- **Airport Map card** — distance banner + zones + position nodes, rendered now from
  an AUH seed layout (`lib/map-seed.ts`); becomes KB-driven when `/map` lands (TDD-04).
- **Structured API Output card** — pretty-printed last backend payload ("API proof").

## Run

```bash
cd frontend
npm install
cp .env.example .env.local         # set NEXT_PUBLIC_API_BASE_URL if not localhost
npm run dev                        # http://localhost:3000
```

Start the backend first:

```bash
cd ../backend
pip install -r requirements.txt -r ../asr_finetuning/requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Confirm STT is live: `curl -s http://127.0.0.1:8000/health` → `"stt_loaded": true`.
Agent/TTS still use stubs; flight data defaults to mock (no keys).

> **Mic note:** browsers only allow microphone capture over **HTTPS or
> `localhost`**. On localhost it works out of the box.

## Scripts

```bash
npm run dev         # dev server
npm run build       # production build
npm run typecheck   # tsc --noEmit
npm run lint        # next lint
```

## Layout

```
frontend/
├── app/
│   ├── layout.tsx        # root layout + Inter font
│   ├── page.tsx          # screen toggle + dashboard state/orchestration
│   └── globals.css       # Tailwind entry + SkyGuide map/progress CSS
├── components/           # LandingPage, TopNav, TicketStrip, Card,
│   │                     #   FlightCard, AgentCard, MapCard, ApiOutputCard
├── hooks/useRecorder.ts  # MediaRecorder mic capture
├── public/assets/        # airport-sky-hero.png (landing hero)
└── lib/
    ├── api.ts            # typed backend client (flight/chat/converse/speak/airports)
    ├── types.ts          # TS mirrors of the backend contracts
    ├── map-seed.ts       # AUH map seed (positions/zones) until /map (TDD-04)
    └── i18n.ts           # RTL helper for Arabic/Darija replies
```

## Configuration

`NEXT_PUBLIC_API_BASE_URL` — backend base URL (default `http://127.0.0.1:8000`).
The client prefixes the relative `audio_url` returned by `/converse` with it.
