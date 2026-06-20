# TDD-05 — Text-to-Speech (Multilingual)

**Component:** `speech/tts/`
**Status:** ⚪ Not started
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
- Pluggable `TTSProvider` interface; default **ElevenLabs**, alt **Azure
  Cognitive Speech**. Selected via `TTS_PROVIDER`.
- Rationale: high-quality multilingual neural voices out of the box; TTS is
  infrastructure, not the graded ML contribution (that's Whisper, TDD-01).

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

- [ ] `TTSProvider` interface + ElevenLabs adapter (+ mock for tests)
- [ ] Language→voice config map
- [ ] `synthesize()` returning bytes + content type
- [ ] `/speak` endpoint glue (TDD-06)
- [ ] (opt) local/offline fallback provider
