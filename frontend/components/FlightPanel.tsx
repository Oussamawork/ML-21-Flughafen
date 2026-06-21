"use client";

import { useEffect, useState } from "react";

import { FlightLookupError, getFlight } from "@/lib/api";
import type { UiLang } from "@/lib/i18n";
import { labels } from "@/lib/i18n";
import type { FlightInfo } from "@/lib/types";

interface Props {
  ui: UiLang;
  airport: string;
}

// Flight number is a typed, structured input (R1) — never parsed from audio.
export function FlightPanel({ ui, airport }: Props) {
  const t = labels(ui);
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [flight, setFlight] = useState<FlightInfo | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Clear stale results when the user switches airports.
  useEffect(() => {
    setFlight(null);
    setErrorMsg(null);
  }, [airport]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const flightNumber = value.trim();
    if (!flightNumber || loading) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await getFlight({ flightNumber, airportId: airport });
      setFlight(res.flight);
    } catch (err) {
      setFlight(null);
      if (err instanceof FlightLookupError && err.kind === "not_found") {
        setErrorMsg(t.flightNotFound);
      } else if (err instanceof FlightLookupError && err.kind === "unavailable") {
        setErrorMsg(t.flightUnavailable);
      } else {
        setErrorMsg(t.error);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <div className="rounded-2xl bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold text-slate-700">{t.flightTitle}</h2>
        <form onSubmit={onSubmit} className="flex gap-2">
          <label className="sr-only" htmlFor="flight-number">
            {t.flightNumberLabel}
          </label>
          <input
            id="flight-number"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={t.flightNumberPlaceholder}
            autoComplete="off"
            className="min-w-0 flex-1 rounded border border-slate-300 px-3 py-2 text-sm uppercase placeholder:normal-case focus:border-brand focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading || !value.trim()}
            className="shrink-0 rounded bg-brand px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {loading ? t.looking : t.lookup}
          </button>
        </form>
        {!flight && !errorMsg && (
          <p className="mt-2 text-xs text-slate-500">{t.flightHint}</p>
        )}
        {errorMsg && <p className="mt-2 text-xs text-rose-600">{errorMsg}</p>}
      </div>

      {flight && <FlightCard ui={ui} flight={flight} />}

      <div className="rounded-2xl border border-dashed border-slate-300 bg-white/50 p-4">
        <h2 className="text-sm font-semibold text-slate-700">{t.mapTitle}</h2>
        <p className="mt-1 text-xs text-slate-400">{t.mapPlaceholder}</p>
      </div>
    </section>
  );
}

function statusColor(status: string | null): string {
  const s = (status ?? "").toLowerCase();
  if (["cancelled", "canceled"].includes(s)) return "bg-rose-100 text-rose-700";
  if (["active", "en-route", "landed"].includes(s)) return "bg-emerald-100 text-emerald-700";
  if (s === "scheduled") return "bg-sky-100 text-sky-700";
  return "bg-slate-100 text-slate-600";
}

function FlightCard({ ui, flight }: { ui: UiLang; flight: FlightInfo }) {
  const t = labels(ui);
  const header = [flight.airline, flight.flight_number].filter(Boolean).join(" ");
  const routePair = [flight.departure_airport, flight.arrival_airport].filter(Boolean);
  return (
    <article className="rounded-2xl bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <span className="text-lg font-semibold text-slate-800">{header}</span>
        {flight.status && (
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(flight.status)}`}>
            {flight.status}
          </span>
        )}
      </div>

      {routePair.length === 2 && (
        <p className="mt-1 text-sm text-slate-500">
          {routePair[0]} → {routePair[1]}
        </p>
      )}

      <div className="mt-3 grid grid-cols-2 gap-2">
        <Tile label={t.gate} value={flight.gate} />
        <Tile label={t.terminal} value={flight.terminal} />
        {flight.scheduled && <Tile label={t.scheduled} value={flight.scheduled} />}
        {flight.estimated && <Tile label={t.estimated} value={flight.estimated} />}
        {flight.baggage && <Tile label={t.baggage} value={flight.baggage} />}
      </div>

      {flight.delay_minutes != null && flight.delay_minutes > 0 && (
        <p className="mt-3 text-sm font-medium text-amber-600">
          {t.delayed.replace("{n}", String(flight.delay_minutes))}
        </p>
      )}
    </article>
  );
}

function Tile({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-base font-semibold text-slate-800">{value ?? "—"}</div>
    </div>
  );
}
