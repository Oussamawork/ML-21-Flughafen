"use client";

import { useEffect, useState } from "react";

import { getMap } from "@/lib/api";
import { NODE_POSITIONS } from "@/lib/map-seed";
import type { MapResponse } from "@/lib/types";

import { Card, SectionTitle } from "./Card";

// Real Zayed International Airport (Terminal A) map as the backdrop, with a
// "You are here" pin + the flight's concourse highlighted (TDD-04 /map). The four
// concourses A/B/C/D are clickable to explore. Map image © airportmaps.com (used
// for this case-study demo). Falls back to the seed coords before the first fetch.
interface Props {
  flightNumber: string;
  position: string;
}

const CONCOURSES = ["concourse-a", "concourse-b", "concourse-c", "concourse-d"];
const letter = (n: string) => n.split("-")[1]?.toUpperCase() ?? n;

export function MapCard({ flightNumber, position }: Props) {
  const [map, setMap] = useState<MapResponse | null>(null);
  const [destination, setDestination] = useState<string | null>(null);

  useEffect(() => setDestination(null), [flightNumber]);

  useEffect(() => {
    let cancelled = false;
    const params = destination
      ? { toNode: destination, position }
      : { flightNumber: flightNumber.trim() || undefined, position };
    getMap(params)
      .then((m) => !cancelled && setMap(m))
      .catch(() => {/* keep the seed shell when the backend is unreachable */});
    return () => {
      cancelled = true;
    };
  }, [flightNumber, position, destination]);

  const positions = map?.positions ?? NODE_POSITIONS;
  const current = map?.current_position ?? position;
  const target = map?.to_node ?? null;
  const gateLabel = map?.gate_label ?? null;
  const routePoints = (map?.route ?? [])
    .map((n) => positions[n])
    .filter(Boolean)
    .map((p) => `${p.x},${p.y}`)
    .join(" ");
  const summary = map?.route_summary;
  const exploring = destination !== null;
  const youPos = positions[current];
  const targetName = target ? map?.nodes?.[target] ?? target : null;

  return (
    <Card className="row-span-2">
      <SectionTitle title="Airport Map" badge={summary ? `${summary.distance_m} m · ${summary.walking_time_min} min` : "Pick a destination"} />
      <div className="mb-2 flex items-baseline justify-between gap-[18px] rounded-lg bg-navy p-3.5 text-white">
        <strong className="text-[30px]">{summary ? `${summary.distance_m} m` : "– m"}</strong>
        <span className="font-[850] text-[#c9d7e8]">
          {summary ? `${summary.walking_time_min} min walk` : "walking time"}
        </span>
      </div>
      <div className="mb-3 flex min-h-[20px] items-center justify-between gap-2 text-[12px] text-muted">
        <span>
          {targetName
            ? `${exploring ? "Exploring" : "Heading"} to ${gateLabel ? `Gate ${gateLabel} · ` : ""}${targetName}`
            : "Tap a concourse to route there"}
        </span>
        {exploring && (
          <button
            type="button"
            onClick={() => setDestination(null)}
            className="rounded-md border border-line bg-white px-2.5 py-1 font-[900] text-[#202938]"
          >
            Back to my gate
          </button>
        )}
      </div>

      {/* Real terminal map backdrop (square, matches the % node coords). */}
      <div className="relative aspect-square w-full overflow-hidden rounded-lg border border-line bg-white">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/assets/terminal-a-map.png"
          alt="Zayed International Airport — Terminal A map"
          className="absolute inset-0 h-full w-full object-contain"
        />

        {/* Dashed route line from "You" to the target gate. */}
        {routePoints && (
          <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            className="pointer-events-none absolute inset-0 z-[5] h-full w-full"
          >
            <polyline
              points={routePoints}
              fill="none"
              stroke="#df1f3d"
              strokeWidth={1.2}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray="2.5 2"
              style={{ filter: "drop-shadow(0 4px 8px rgba(223,31,61,.3))" }}
            />
          </svg>
        )}

        {/* Concourse markers (A/B/C/D) — clickable; target highlighted. */}
        {CONCOURSES.map((node) => {
          const p = positions[node];
          if (!p) return null;
          const isTarget = node === target;
          const size = isTarget ? "h-9 w-9 text-[11px]" : "h-7 w-7 text-[10px]";
          const bg = isTarget ? "bg-red" : "bg-blue/85";
          const ring = isTarget
            ? "shadow-[0_0_0_6px_rgba(223,31,61,.18),0_10px_22px_rgba(223,31,61,.32)]"
            : "shadow-[0_6px_16px_rgba(38,68,102,.28)]";
          return (
            <button
              key={node}
              type="button"
              title={`Route to ${map?.nodes?.[node] ?? node}`}
              onClick={() => setDestination(node)}
              style={{ left: `${p.x}%`, top: `${p.y}%` }}
              className={`absolute z-10 grid -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border-2 border-white font-[950] text-white transition hover:scale-[1.12] ${size} ${bg} ${ring}`}
            >
              {isTarget && gateLabel ? gateLabel : letter(node)}
            </button>
          );
        })}

        {/* "You are here" pin. */}
        {youPos && (
          <div
            style={{ left: `${youPos.x}%`, top: `${youPos.y}%` }}
            className="absolute z-20 grid h-9 w-9 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border-2 border-white bg-green text-[10px] font-[950] text-white shadow-[0_0_0_7px_rgba(29,155,117,.18),0_12px_24px_rgba(29,155,117,.32)]"
          >
            You
          </div>
        )}
      </div>
      <p className="mt-2 text-[10px] text-muted">Map © airportmaps.com — case-study demo</p>
    </Card>
  );
}
