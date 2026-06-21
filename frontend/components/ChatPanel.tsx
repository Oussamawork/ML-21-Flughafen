"use client";

import { useEffect, useRef } from "react";

import type { UiLang } from "@/lib/i18n";
import { labels } from "@/lib/i18n";
import type { Message } from "@/lib/types";

import { MessageBubble } from "./MessageBubble";

interface Props {
  messages: Message[];
  ui: UiLang;
  thinking: boolean;
}

export function ChatPanel({ messages, ui, thinking }: Props) {
  const t = labels(ui);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  return (
    <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
      {messages.length === 0 && (
        <p className="mt-10 text-center text-sm text-slate-500">{t.emptyHint}</p>
      )}
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} ui={ui} />
      ))}
      {thinking && (
        <div className="flex justify-start">
          <div className="rounded-2xl bg-white px-4 py-2 text-sm text-slate-500 shadow-sm">
            {t.thinking}
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
