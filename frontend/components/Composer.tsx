"use client";

import { useState } from "react";

import { useRecorder } from "@/hooks/useRecorder";
import type { UiLang } from "@/lib/i18n";
import { labels, uiDir } from "@/lib/i18n";

interface Props {
  ui: UiLang;
  disabled: boolean;
  onSendText: (text: string) => void;
  onSendAudio: (audio: Blob) => void;
}

export function Composer({ ui, disabled, onSendText, onSendAudio }: Props) {
  const t = labels(ui);
  const [text, setText] = useState("");
  const recorder = useRecorder();

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSendText(trimmed);
    setText("");
  };

  const toggleMic = async () => {
    if (recorder.recording) {
      const blob = await recorder.stop();
      if (blob && blob.size > 0) onSendAudio(blob);
    } else {
      await recorder.start().catch(() => {});
    }
  };

  return (
    <div className="border-t bg-white px-4 py-3">
      <div className="mx-auto flex max-w-3xl items-center gap-2">
        <button
          onClick={toggleMic}
          disabled={disabled}
          title={recorder.recording ? t.stop : t.tapToSpeak}
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-lg transition ${
            recorder.recording
              ? "animate-pulse bg-red-600 text-white"
              : "bg-brand text-white hover:bg-brand-dark"
          } disabled:opacity-50`}
          aria-label={recorder.recording ? t.stop : t.tapToSpeak}
        >
          {recorder.recording ? "■" : "🎤"}
        </button>

        <input
          value={text}
          dir={uiDir(ui)}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder={recorder.recording ? t.listening : t.placeholder}
          disabled={disabled || recorder.recording}
          className="h-11 flex-1 rounded-full border border-slate-300 px-4 outline-none focus:border-brand"
        />

        <button
          onClick={submit}
          disabled={disabled || !text.trim()}
          className="h-11 shrink-0 rounded-full bg-brand px-5 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {t.send}
        </button>
      </div>
      {recorder.error && (
        <p className="mx-auto mt-2 max-w-3xl text-xs text-red-600">
          {recorder.error}
        </p>
      )}
    </div>
  );
}
