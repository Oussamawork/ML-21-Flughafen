# TDD-05 — Text-to-Speech (Multilingual)

**Component:** `backend/app/services/tts.py`
**Status:** 🟢 Built — real **local** neural TTS (Meta **MMS-TTS** via the installed
`transformers`/`torch`, on CPU, **no key**, default `TTS_PROVIDER=local`); behind the
existing `TTS` interface so `/speak` + `/converse` and the frontend autoplay are
unchanged. ar/fr/en voices; Darija→Arabic. Live-verified. Hosted ElevenLabs/Azure
remain a clean drop-in behind the same interface.
**Depends on:** TDD-02 (produces text+language) · **Consumed by:** TDD-06 (`/speak`)

---

## 1. Purpose

Convert the agent's textual answer into natural speech in the passenger's
language for hands-free interaction.

## 2. Requirements satisfied

- *Multilingual STT/TTS pipeline supporting Arabic, English, French, Darija.*
- *Respond vocally* (proposal example interaction).

## 3. Design

### 3.1 Provider
- Pluggable `TTS` interface, selected via `TTS_PROVIDER`. **Default `local` = Meta
  **MMS-TTS** (`facebook/mms-tts-{ara,fra,eng}`) run locally on CPU via the
  `transformers`/`torch` stack already pulled by the ASR path — **no API key, fully
  offline** (same philosophy as the fine-tuned Whisper). `stub` = silent WAV (tests).
- Rationale: keeps the whole pipeline runnable offline/key-free (the project's hard
  rule); TTS is infrastructure, not the graded ML contribution (that's Whisper,
  TDD-01). **Hosted ElevenLabs/Azure** stay available behind the same interface for
  premium quality when a key is wired (not built in v1).
- One model **per language**, lazy-loaded + cached for the process; a bounded phrase
  cache makes replays/identical answers instant (the latency note in §6).

### 3.2 Language → voice mapping
```yaml
voices:
  ar:  { provider_voice: "<arabic voice id>" }
  ary: { provider_voice: "<arabic voice id>" }   # Darija → Arabic voice
  fr:  { provider_voice: "<french voice id>" }
  en:  { provider_voice: "<english voice id>" }
```
- Config-driven; no voice ids hard-coded in code.
- Darija TTS support is limited across providers → fall back to an Arabic voice
  (documented limitation; acceptable since input-side Darija is the ML focus).

### 3.3 Output
- Format: MP3 (default) or WAV; returns audio bytes + `content_type`.
- Optional streaming for low latency (provider-dependent); v1 may return the full
  clip.

## 4. Interfaces & data contracts

```python
class TTSProvider(Protocol):
    def synthesize(self, text: str, language: str) -> TTSResult

# TTSResult
{ "audio": b"...", "content_type": "audio/mpeg", "language": "ar",
  "voice": "<id>", "provider": "elevenlabs" }
```
Backend endpoint (TDD-06): `POST /speak` `{text, language}` → audio stream.

## 5. Dependencies

Provider SDK/HTTP (`elevenlabs` or `azure-cognitiveservices-speech` / REST),
`httpx`. Env: `TTS_PROVIDER`, `TTS_API_KEY`, voice-map config.

## 6. Open questions / risks

- **Darija voice quality** — likely use Arabic voice; note in eval/limitations.
- **Latency/cost** of neural TTS in the live demo → cache identical phrases;
  consider local fallback (e.g. Coqui/espeak) for offline demo resilience.
- **Audio format** the frontend can autoplay (MP3 broadly supported).

## 7. Task checklist

- [x] `TTS` interface + **local MMS-TTS** provider (+ `StubTTS` for tests)
- [x] Language→model map (config-driven; `ary`→ar voice; `TTS_MODEL_<LANG>` overrides)
- [x] `synthesize()` returning WAV bytes + content type (float→16-bit PCM); phrase cache
- [x] `/speak` + `/converse` glue (TDD-06) — already wired; no change needed
- [x] Tests (`tests/test_tts.py`, MMS engine faked → no model download); 61 backend tests
- [ ] (opt) hosted ElevenLabs/Azure adapter for premium quality (same interface)
- Notes: MMS Arabic mispronounces embedded Latin (e.g. gate "B12"); Darija uses the
  Arabic voice — both acceptable (TTS is infra; the owned Darija model is Whisper).
