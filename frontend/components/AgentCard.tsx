"use client";

import { useEffect, useRef, useState } from "react";

import { useRecorder } from "@/hooks/useRecorder";
import { isRtl } from "@/lib/i18n";

import { Card, SectionTitle } from "./Card";

export interface AgentMessage {
  role: "Passenger" | "SkyGuide";
  text: string;
  language?: string;
}

// Mirrors SkyGuide's .agent-card, plus our mic capture (fine-tuned Whisper).
interface Props {
  messages: AgentMessage[];
  badge: string;
  thinking: boolean;
  autoSpeak: boolean;
  onAutoSpeak: (v: boolean) => void;
  onReplay: () => void;
  onAsk: (text: string) => void;
  onAudio: (blob: Blob) => void;
  placeholder: string;
  rtl: boolean;
}

export function AgentCard({
  messages,
  badge,
  thinking,
  autoSpeak,
  onAutoSpeak,
  onReplay,
  onAsk,
  onAudio,
  placeholder,
  rtl,
}: Props) {
  const [text, setText] = useState("");
  const recorder = useRecorder();
  const listRef = useRef<HTMLDivElement>(null);

  // Scroll only the messages box to the newest line — never the whole page
  // (scrollIntoView would scroll every ancestor, yanking the window down).
  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, thinking]);

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || thinking) return;
    onAsk(trimmed);
    setText("");
  };

  const toggleMic = async () => {
    if (recorder.recording) {
      const blob = await recorder.stop();
      if (blob && blob.size > 0) onAudio(blob);
    } else {
      await recorder.start().catch(() => {});
    }
  };

  return (
    <Card>
      <SectionTitle title="Airport Agent" badge={badge} />

      <div className="mb-2.5 flex items-center justify-between gap-2.5">
        <label className="inline-flex items-center gap-2 text-[13px] text-[#3f4a58]">
          <input
            type="checkbox"
            checked={autoSpeak}
            onChange={(e) => onAutoSpeak(e.target.checked)}
            className="h-auto w-auto"
          />
          Voice over
        </label>
        <button
          type="button"
          onClick={onReplay}
          className="min-h-[34px] rounded-lg border border-line bg-white px-[11px] text-xs font-[900] text-[#202938]"
        >
          Replay voice
        </button>
      </div>

      <div ref={listRef} className="grid h-[190px] content-start gap-2 overflow-auto rounded-lg border border-line bg-white p-3">
        {messages.map((m, i) => (
          <p
            key={i}
            dir={isRtl(m.language) ? "rtl" : "ltr"}
            className="m-0 leading-[1.45]"
          >
            <strong>{m.role}:</strong> {m.text}
          </p>
        ))}
        {thinking && <p className="m-0 leading-[1.45] text-muted">SkyGuide: …</p>}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="mt-3 grid grid-cols-[auto_1fr_auto] gap-2.5 max-[640px]:grid-cols-1"
      >
        <button
          type="button"
          onClick={toggleMic}
          title={recorder.recording ? "Stop" : "Speak"}
          aria-label={recorder.recording ? "Stop recording" : "Record question"}
          className={`grid min-h-[48px] w-12 place-items-center rounded-lg text-lg text-white ${
            recorder.recording ? "animate-pulse bg-red" : "bg-blue"
          } max-[640px]:w-full`}
        >
          {recorder.recording ? "■" : "🎤"}
        </button>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          dir={rtl ? "rtl" : "ltr"}
          placeholder={recorder.recording ? "Listening…" : placeholder}
          disabled={recorder.recording}
          className="min-h-[48px] w-full rounded-lg border border-line bg-white px-3 font-[800] text-ink"
        />
        <button
          type="submit"
          disabled={thinking || !text.trim()}
          className="min-h-[48px] min-w-[74px] rounded-lg bg-blue px-3 font-[950] text-white disabled:opacity-60"
        >
          Ask
        </button>
      </form>
      {recorder.error && (
        <p className="mt-2 text-xs text-red">{recorder.error}</p>
      )}
    </Card>
  );
}
