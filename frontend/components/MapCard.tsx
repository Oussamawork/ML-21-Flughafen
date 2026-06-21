"use client";

import { useEffect, useState } from "react";

import { getMap } from "@/lib/api";
import { NODE_POSITIONS } from "@/lib/map-seed";
import type { MapResponse } from "@/lib/types";

import { Card, SectionTitle } from "./Card";

// Real Zayed International Airport (Terminal A) map as the backdrop, with every
// gate A1..D49 marked along its concourse (hover for the code) and the flight's
// gate pinned in red. Click any gate to route there. Map © airportmaps.com
// (case-study demo). Falls back to the seed coords before the first fetch.
interface Props {
  flightNumber: string;
  position: string;
}

const normGate = (g?: string | null) =>
  g ? g.toUpperCase().replace(/^([A-Z]+)0*(\d+)$/, "$1$2") : "";

export function MapCard({ flightNumber, position }: Props) {
  const [map, setMap] = useState<MapResponse | null>(null);
  const [destGate, setDestGate] = useState<string | null>(null); // clicked gate

  useEffect(() => setDestGate(null), [flightNumber]);

  useEffect(() => {
    let cancelled = false;
    const params = destGate
      ? { gate: destGate, position }
      : { flightNumber: flightNumber.trim() || undefined, position };
    getMap(params)
      .then((m) => !cancelled && setMap(m))
      .catch(() => {/* keep the seed shell when the backend is unreachable */});
    return () => {
      cancelled = true;
    };
  }, [flightNumber, position, destGate]);

  const positions = map?.positions ?? NODE_POSITIONS;
  const gates = map?.gates ?? [];
  const current = map?.current_position ?? position;
  const activeGate = normGate(map?.gate_label);
  const summary = map?.route_summary;
  const exploring = destGate !== null;
  const youPos = positions[current];
  const targetName = map?.to_node ? map?.nodes?.[map.to_node] ?? map.to_node : null;

  return (
    <Card className="row-span-2">
      <SectionTitle title="Airport Map" badge={summary ? `${summary.distance_m} m · ${summary.walking_time_min} min` : "Pick a gate"} />
      <div className="mb-2 flex items-baseline justify-between gap-[18px] rounded-lg bg-navy p-3.5 text-white">
        <strong className="text-[30px]">{summary ? `${summary.distance_m} m` : "– m"}</strong>
        <span className="font-[850] text-[#c9d7e8]">
          {summary ? `${summary.walking_time_min} min walk` : "walking time"}
        </span>
      </div>
      <div className="mb-3 flex min-h-[20px] items-center justify-between gap-2 text-[12px] text-muted">
        <span>
          {map?.gate_label
            ? `${exploring ? "Exploring" : "Heading"} to Gate ${map.gate_label} · ${targetName}`
            : "Tap any gate to route there"}
        </span>
        {exploring && (
          <button
            type="button"
            onClick={() => setDestGate(null)}
            className="rounded-md border border-line bg-white px-2.5 py-1 font-[900] text-[#202938]"
          >
            Back to my gate
          </button>
        )}
      </div>

      <div className="relative aspect-square w-full overflow-hidden rounded-lg border border-line bg-white">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/assets/terminal-a-map.png"
          alt="Zayed International Airport — Terminal A map"
          className="absolute inset-0 h-full w-full object-contain"
        />

        {/* Every gate A1..D49 (hover for the code); click to route there. */}
        {gates.map((g) => {
          const isActive = normGate(g.code) === activeGate;
          if (isActive) return null; // drawn as the bold pin below
          return (
            <button
              key={g.code}
              type="button"
              title={`Gate ${g.code}`}
              onClick={() => setDestGate(g.code)}
              style={{ left: `${g.x}%`, top: `${g.y}%` }}
              className="absolute z-10 h-[11px] w-[11px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-white bg-blue/80 shadow-[0_2px_5px_rgba(38,68,102,.35)] transition hover:h-[15px] hover:w-[15px] hover:bg-blue"
            />
          );
        })}

        {/* The flight's / selected gate — bold red pin with its code. */}
        {map?.gate_position && map?.gate_label && (
          <div
            style={{ left: `${map.gate_position.x}%`, top: `${map.gate_position.y}%` }}
            className="absolute z-30 grid h-8 min-w-8 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border-2 border-white bg-red px-1.5 text-[11px] font-[950] text-white shadow-[0_0_0_6px_rgba(223,31,61,.18),0_10px_22px_rgba(223,31,61,.34)]"
          >
            {map.gate_label}
          </div>
        )}

        {/* "You are here" pin. */}
        {youPos && (
          <div
            style={{ left: `${youPos.x}%`, top: `${youPos.y}%` }}
            className="absolute z-20 grid h-8 w-8 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border-2 border-white bg-green text-[10px] font-[950] text-white shadow-[0_0_0_6px_rgba(29,155,117,.18),0_10px_22px_rgba(29,155,117,.32)]"
          >
            You
          </div>
        )}
      </div>
      <p className="mt-2 text-[10px] text-muted">Map © airportmaps.com — case-study demo</p>
    </Card>
  );
}
