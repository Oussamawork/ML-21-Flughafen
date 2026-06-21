"use client";

import { useState } from "react";

import type { UiLang } from "@/lib/i18n";
import { isRtl, labels } from "@/lib/i18n";
import type { Message } from "@/lib/types";

interface Props {
  message: Message;
  ui: UiLang;
}

export function MessageBubble({ message, ui }: Props) {
  const t = labels(ui);
  const [showTrace, setShowTrace] = useState(false);
  const isUser = message.role === "user";
  const dir = isRtl(message.language) ? "rtl" : "ltr";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2 shadow-sm ${
          isUser ? "bg-brand text-white" : "bg-white text-slate-900"
        }`}
      >
        <div className="mb-0.5 flex items-center gap-2 text-[10px] uppercase opacity-60">
          <span>{isUser ? t.you : t.assistant}</span>
          {message.language && <span>· {message.language}</span>}
          {message.intent && <span>· {message.intent}</span>}
        </div>
        <p dir={dir} className="whitespace-pre-wrap break-words leading-relaxed">
          {message.text}
        </p>

        {message.audioUrl && (
          <audio
            className="mt-2 h-8 w-full"
            controls
            autoPlay
            src={message.audioUrl}
          />
        )}

        {message.toolTrace && message.toolTrace.length > 0 && (
          <div className="mt-2 text-xs">
            <button
              onClick={() => setShowTrace((v) => !v)}
              className="text-brand underline-offset-2 hover:underline"
            >
              {showTrace ? "▾" : "▸"} {t.toolTrace} ({message.toolTrace.length})
            </button>
            {showTrace && (
              <pre className="mt-1 overflow-x-auto rounded bg-slate-50 p-2 text-[11px] text-slate-700">
                {JSON.stringify(message.toolTrace, null, 2)}
              </pre>
            )}
          </div>
        )}

        {message.latencyMs && Object.keys(message.latencyMs).length > 0 && (
          <div className="mt-1 text-[10px] opacity-50">
            {Object.entries(message.latencyMs)
              .map(([k, v]) => `${k} ${v}ms`)
              .join(" · ")}
          </div>
        )}
      </div>
    </div>
  );
}
