# Frontend — Web Demo (TDD-07)

The demo UI for the Smart Airport Wayfinding Assistant: a multilingual **voice +
text** chat that talks to the FastAPI backend (TDD-06). Design:
`../docs/tdd/TDD-07-Frontend.md`.

Next.js (App Router) + React + TypeScript + Tailwind.

## Features

- **Text + voice** input. Mic capture via `MediaRecorder` → `POST /converse`
  (STT → agent → TTS); typed input → `POST /chat`, then `POST /speak` for audio.
- **Auto-plays** the spoken reply; shows the transcript and the detected language.
- **RTL/LTR** rendering per message (Arabic/Darija right-to-left).
- **UI language** toggle (EN / FR / AR) for the surrounding labels.
- **Airport selector** populated from `GET /airports` (proves airport-agnostic).
- **Tool-trace** panel per assistant message + per-stage latency (great for the
  demo narrative / TDD-08).

## Run

```bash
cd frontend
npm install
cp .env.example .env.local         # set NEXT_PUBLIC_API_BASE_URL if not localhost
npm run dev                        # http://localhost:3000
```

Start the backend first (`cd ../backend && uvicorn app.main:app --reload`). The
backend runs with offline stubs, so the full round-trip works with no GPU/keys.

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
│   ├── layout.tsx        # root layout + metadata
│   ├── page.tsx          # main chat page (state + orchestration)
│   └── globals.css       # Tailwind entry
├── components/           # Header, ChatPanel, MessageBubble, Composer
├── hooks/useRecorder.ts  # MediaRecorder mic capture
└── lib/
    ├── api.ts            # typed backend client (chat/converse/speak/airports)
    ├── types.ts          # TS mirrors of the backend contracts
    └── i18n.ts           # UI labels (en/fr/ar) + RTL helper
```

## Configuration

`NEXT_PUBLIC_API_BASE_URL` — backend base URL (default `http://127.0.0.1:8000`).
The client prefixes the relative `audio_url` returned by `/converse` with it.
