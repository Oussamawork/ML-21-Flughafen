"use client";

import { useCallback, useEffect, useState } from "react";

import { ChatPanel } from "@/components/ChatPanel";
import { Composer } from "@/components/Composer";
import { Header } from "@/components/Header";
import { converse, getAirports, sendChat, speak } from "@/lib/api";
import type { UiLang } from "@/lib/i18n";
import { labels, uiDir } from "@/lib/i18n";
import type { Message } from "@/lib/types";

function uid(): string {
  return Math.random().toString(36).slice(2);
}

export default function Page() {
  const [ui, setUi] = useState<UiLang>("en");
  const [airports, setAirports] = useState<string[]>(["AUH"]);
  const [airport, setAirport] = useState("AUH");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [thinking, setThinking] = useState(false);

  const t = labels(ui);

  // Load the airport list from the backend (proves airport-agnostic design).
  useEffect(() => {
    getAirports()
      .then((res) => {
        setAirports(res.airports);
        setAirport((cur) => (res.airports.includes(cur) ? cur : res.default));
      })
      .catch(() => {/* backend offline: keep defaults */});
  }, []);

  const push = useCallback((m: Message) => setMessages((ms) => [...ms, m]), []);

  const handleError = useCallback(() => {
    push({ id: uid(), role: "assistant", text: t.error });
  }, [push, t.error]);

  const onSendText = useCallback(
    async (text: string) => {
      push({ id: uid(), role: "user", text });
      setThinking(true);
      try {
        const res = await sendChat({ text, sessionId, airportId: airport });
        setSessionId(res.session_id);
        let audioUrl: string | undefined;
        try {
          audioUrl = await speak(res.answer, res.language);
        } catch {/* TTS optional */}
        push({
          id: uid(),
          role: "assistant",
          text: res.answer,
          language: res.language,
          intent: res.intent,
          toolTrace: res.tool_trace,
          latencyMs: res.latency_ms,
          audioUrl,
        });
      } catch {
        handleError();
      } finally {
        setThinking(false);
      }
    },
    [airport, handleError, push, sessionId],
  );

  const onSendAudio = useCallback(
    async (audio: Blob) => {
      setThinking(true);
      try {
        const res = await converse({ audio, sessionId });
        setSessionId(res.session_id);
        push({ id: uid(), role: "user", text: res.text_in, language: res.language });
        push({
          id: uid(),
          role: "assistant",
          text: res.answer,
          language: res.language,
          intent: res.intent,
          toolTrace: res.tool_trace,
          latencyMs: res.latency_ms,
          audioUrl: res.audio_url,
        });
      } catch {
        handleError();
      } finally {
        setThinking(false);
      }
    },
    [handleError, push, sessionId],
  );

  return (
    <main dir={uiDir(ui)} className="mx-auto flex h-dvh max-w-3xl flex-col bg-slate-50">
      <Header
        ui={ui}
        onUiChange={setUi}
        airports={airports}
        airport={airport}
        onAirportChange={setAirport}
      />
      <ChatPanel messages={messages} ui={ui} thinking={thinking} />
      <Composer
        ui={ui}
        disabled={thinking}
        onSendText={onSendText}
        onSendAudio={onSendAudio}
      />
    </main>
  );
}
