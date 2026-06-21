"use client";

import { useCallback, useEffect, useState } from "react";

import { AgentCard, type AgentMessage } from "@/components/AgentCard";
import { ApiOutputCard } from "@/components/ApiOutputCard";
import { FlightCard } from "@/components/FlightCard";
import { LandingPage } from "@/components/LandingPage";
import { MapCard } from "@/components/MapCard";
import { TicketStrip, type Position, type UiLanguage } from "@/components/TicketStrip";
import { TopNav } from "@/components/TopNav";
import {
  FlightLookupError,
  converse,
  getFlight,
  sendChat,
  speak,
} from "@/lib/api";
import type { FlightInfo, Language } from "@/lib/types";

// SkyGuide's language select -> our backend language codes (darija = ary).
function toLang(ui: UiLanguage): Language {
  if (ui === "fr") return "fr";
  if (ui === "darija") return "ary";
  return "en";
}

function play(url: string) {
  new Audio(url).play().catch(() => {});
}

export default function Page() {
  const [screen, setScreen] = useState<"home" | "app">("home");
  const [flightNumber, setFlightNumber] = useState("");
  const [language, setLanguage] = useState<UiLanguage>("en");
  const [position, setPosition] = useState<Position>("entrance");

  const [flight, setFlight] = useState<FlightInfo | null>(null);
  const [checkin, setCheckin] = useState<string | null>(null);
  const [payload, setPayload] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);

  const [messages, setMessages] = useState<AgentMessage[]>([
    { role: "SkyGuide", text: 'Ask me: "How much left for the gate?"' },
  ]);
  const [thinking, setThinking] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [lastSpoken, setLastSpoken] = useState("");
  const [badge, setBadge] = useState("DL model");
  const [sessionId, setSessionId] = useState<string | undefined>();

  const addAgent = useCallback((m: AgentMessage) => {
    setMessages((ms) => [...ms, m]);
  }, []);

  // Probe the backend for the agent badge (STT model) + API-online state.
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"}/health`)
      .then((r) => (r.ok ? r.json() : null))
      .then((h) => {
        if (!h) return;
        setApiOnline(true);
        if (h.stt_loaded && h.whisper_model) setBadge(`STT: ${h.whisper_model}`);
      })
      .catch(() => setApiOnline(false));
  }, []);

  const loadFlight = useCallback(async () => {
    const n = flightNumber.trim();
    if (!n) return;
    setLoading(true);
    try {
      const res = await getFlight({ flightNumber: n, position });
      setFlight(res.flight);
      setCheckin(res.checkin?.zone ?? null);
      setPayload(res);
      setApiOnline(true);
    } catch (err) {
      setFlight(null);
      setCheckin(null);
      if (err instanceof FlightLookupError && err.kind === "not_found") {
        addAgent({ role: "SkyGuide", text: `No flight found for ${n} at this airport.` });
      } else if (err instanceof FlightLookupError && err.kind === "unavailable") {
        addAgent({ role: "SkyGuide", text: "Flight data is temporarily unavailable." });
      } else {
        addAgent({ role: "SkyGuide", text: "Something went wrong. Is the backend running?" });
      }
    } finally {
      setLoading(false);
    }
  }, [flightNumber, position, addAgent]);

  // Load the flight as soon as we enter the app (mirrors SkyGuide's showApp()).
  const enterApp = useCallback(() => {
    setScreen("app");
    void loadFlight();
  }, [loadFlight]);

  const onAsk = useCallback(
    async (text: string) => {
      addAgent({ role: "Passenger", text });
      setThinking(true);
      try {
        const res = await sendChat({
          text,
          sessionId,
          language: toLang(language),
          flightNumber: flightNumber.trim() || undefined,
          position,
        });
        setSessionId(res.session_id);
        setPayload(res);
        addAgent({ role: "SkyGuide", text: res.answer, language: res.language });
        setLastSpoken(res.answer);
        if (autoSpeak) {
          try {
            play(await speak(res.answer, res.language));
          } catch {/* TTS optional */}
        }
      } catch {
        addAgent({ role: "SkyGuide", text: "Agent error. Is the backend running?" });
      } finally {
        setThinking(false);
      }
    },
    [addAgent, sessionId, language, autoSpeak, flightNumber, position],
  );

  const onAudio = useCallback(
    async (audio: Blob) => {
      setThinking(true);
      try {
        const res = await converse({
          audio,
          sessionId,
          flightNumber: flightNumber.trim() || undefined,
          position,
        });
        setSessionId(res.session_id);
        setPayload(res);
        addAgent({ role: "Passenger", text: res.text_in, language: res.language });
        addAgent({ role: "SkyGuide", text: res.answer, language: res.language });
        setLastSpoken(res.answer);
        if (autoSpeak && res.audio_url) play(res.audio_url);
      } catch {
        addAgent({ role: "SkyGuide", text: "Voice error. Is the backend running?" });
      } finally {
        setThinking(false);
      }
    },
    [addAgent, sessionId, autoSpeak, flightNumber, position],
  );

  const onReplay = useCallback(async () => {
    const text = lastSpoken || "Ask me a question first.";
    try {
      play(await speak(text, toLang(language)));
    } catch {/* TTS optional */}
  }, [lastSpoken, language]);

  if (screen === "home") return <LandingPage onEnter={enterApp} />;

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#f7fbff,#edf3f7)]">
      <div className="sg-progress" data-on={loading ? "true" : "false"} />
      <TopNav variant="app" onHome={() => setScreen("home")} />

      <TicketStrip
        flightNumber={flightNumber}
        onFlightNumber={setFlightNumber}
        language={language}
        onLanguage={setLanguage}
        position={position}
        onPosition={setPosition}
        onLoad={loadFlight}
        loading={loading}
      />

      <section className="mx-auto grid max-w-[1240px] grid-cols-[.85fr_1.15fr] gap-[18px] px-[clamp(18px,4vw,58px)] pb-[46px] max-[980px]:grid-cols-1">
        <FlightCard flight={flight} checkin={checkin} loading={loading} apiOnline={apiOnline} />
        <AgentCard
          messages={messages}
          badge={badge}
          thinking={thinking}
          autoSpeak={autoSpeak}
          onAutoSpeak={setAutoSpeak}
          onReplay={onReplay}
          onAsk={onAsk}
          onAudio={onAudio}
        />
        <MapCard flightNumber={flightNumber} position={position} />
        <ApiOutputCard payload={payload} />
      </section>
    </div>
  );
}
