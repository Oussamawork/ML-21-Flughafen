"use client";

import type { UiLang } from "@/lib/i18n";
import { labels } from "@/lib/i18n";

interface Props {
  ui: UiLang;
  onUiChange: (ui: UiLang) => void;
  airports: string[];
  airport: string;
  onAirportChange: (airport: string) => void;
}

const UI_OPTIONS: { value: UiLang; label: string }[] = [
  { value: "en", label: "EN" },
  { value: "fr", label: "FR" },
  { value: "ar", label: "ع" },
];

export function Header({
  ui,
  onUiChange,
  airports,
  airport,
  onAirportChange,
}: Props) {
  const t = labels(ui);
  return (
    <header className="bg-brand text-white shadow">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
        <div className="min-w-0">
          <h1 className="truncate text-lg font-semibold">✈️ {t.title}</h1>
          <p className="truncate text-xs text-teal-100">{t.subtitle}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <label className="sr-only" htmlFor="airport">
            {t.airport}
          </label>
          <select
            id="airport"
            value={airport}
            onChange={(e) => onAirportChange(e.target.value)}
            className="rounded bg-brand-dark px-2 py-1 text-sm"
          >
            {airports.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
          <div className="flex overflow-hidden rounded border border-teal-200/40">
            {UI_OPTIONS.map((o) => (
              <button
                key={o.value}
                onClick={() => onUiChange(o.value)}
                className={`px-2 py-1 text-sm ${
                  ui === o.value ? "bg-white text-brand" : "bg-brand-dark"
                }`}
                aria-pressed={ui === o.value}
              >
                {o.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}
