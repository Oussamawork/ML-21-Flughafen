"use client";

import { useEffect, useState } from "react";

import { getMap } from "@/lib/api";
import { NODE_POSITIONS, ZONES, shortNode } from "@/lib/map-seed";
import type { MapResponse } from "@/lib/types";

import { Card, SectionTitle } from "./Card";

// Mirrors SkyGuide's .map-card: live layout + route from /map (TDD-04). Falls back
// to the static AUH seed before the first fetch (or if the backend is offline).
interface Props {
  flightNumber: string;
  position: string;
}

export function MapCard({ flightNumber, position }: Props) {
  const [map, setMap] = useState<MapResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    getMap({ flightNumber: flightNumber.trim() || undefined, position })
      .then((m) => !cancelled && setMap(m))
      .catch(() => {/* keep the seed shell when the backend is unreachable */});
    return () => {
      cancelled = true;
    };
  }, [flightNumber, position]);

  const positions = map?.positions ?? NODE_POSITIONS;
  const zones = map?.zones ?? ZONES.map((z) => ({ label: z.label, ...z.style }));
  const route = map?.route ?? [];
  const onRoute = new Set(route);
  const current = map?.current_position ?? position;
  const target = map?.to_node ?? (route.length ? route[route.length - 1] : null);
  const summary = map?.route_summary;

  // Route polyline points in the 0-100 viewBox.
  const points = route
    .map((n) => positions[n])
    .filter(Boolean)
    .map((p) => `${p.x},${p.y}`)
    .join(" ");

  return (
    <Card className="row-span-2">
      <SectionTitle title="Airport Map" badge={summary ? `${summary.distance_m} m left` : "No route yet"} />
      <div className="mb-3 flex items-baseline justify-between gap-[18px] rounded-lg bg-navy p-3.5 text-white">
        <strong className="text-[30px]">{summary ? `${summary.distance_m} m` : "- m"}</strong>
        <span className="font-[850] text-[#c9d7e8]">
          {summary ? `${summary.walking_time_min} min walk` : "walking time"}
        </span>
      </div>
      <div className="sg-map-grid relative min-h-[500px] overflow-hidden rounded-lg border border-line max-[640px]:min-h-[420px]">
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="pointer-events-none absolute inset-0 h-full w-full"
        >
          {points && (
            <polyline
              points={points}
              fill="none"
              stroke="#df1f3d"
              strokeWidth={1.4}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray="3 2"
              style={{ filter: "drop-shadow(0 6px 10px rgba(223,31,61,.28))" }}
            />
          )}
        </svg>
        {zones.map((z) => (
          <div
            key={z.label}
            className="absolute grid place-items-center rounded-lg border border-black/10 bg-white/[.62] text-xs font-[950] uppercase text-[#405066]"
            style={{ left: `${z.x}%`, top: `${z.y}%`, width: `${z.w}%`, height: `${z.h}%` }}
          >
            {z.label}
          </div>
        ))}
        {Object.entries(positions).map(([node, p]) => {
          const isCurrent = node === current;
          const isTarget = node === target;
          const isActive = onRoute.has(node);
          const size = isCurrent || isTarget ? "h-[42px] w-[42px]" : "h-[34px] w-[34px]";
          const bg = isCurrent ? "bg-green" : isTarget ? "bg-red" : isActive ? "bg-blue" : "bg-[#8aa0b7]";
          const ring = isCurrent
            ? "shadow-[0_0_0_8px_rgba(29,155,117,.16),0_14px_26px_rgba(29,155,117,.28)]"
            : isTarget
              ? "shadow-[0_0_0_8px_rgba(223,31,61,.16),0_14px_28px_rgba(223,31,61,.3)]"
              : "shadow-[0_10px_22px_rgba(38,68,102,.2)]";
          return (
            <button
              key={node}
              type="button"
              title={node}
              style={{ left: `${p.x}%`, top: `${p.y}%` }}
              className={`absolute -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white text-[10px] font-[950] text-white transition hover:scale-[1.14] ${size} ${bg} ${ring}`}
            >
              {shortNode(node)}
            </button>
          );
        })}
      </div>
    </Card>
  );
}
