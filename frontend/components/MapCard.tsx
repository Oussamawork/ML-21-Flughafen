"use client";

import { NODE_POSITIONS, ZONES, shortNode } from "@/lib/map-seed";

import { Card, SectionTitle } from "./Card";

// Mirrors SkyGuide's .map-card. Shell only: shows the current position from the
// "I am here" selector; route + distance arrive with /map (TDD-04).
interface Props {
  current: string;
}

export function MapCard({ current }: Props) {
  return (
    <Card className="row-span-2">
      <SectionTitle title="Airport Map" badge="No route yet" />
      <div className="mb-3 flex items-baseline justify-between gap-[18px] rounded-lg bg-navy p-3.5 text-white">
        <strong className="text-[30px]">- m</strong>
        <span className="font-[850] text-[#c9d7e8]">walking time</span>
      </div>
      <div className="sg-map-grid relative min-h-[500px] overflow-hidden rounded-lg border border-line max-[640px]:min-h-[420px]">
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="pointer-events-none absolute inset-0 h-full w-full"
        />
        {ZONES.map((z) => (
          <div
            key={z.label}
            className="absolute grid place-items-center rounded-lg border border-black/10 bg-white/[.62] text-xs font-[950] uppercase text-[#405066]"
            style={{
              left: `${z.style.x}%`,
              top: `${z.style.y}%`,
              width: `${z.style.w}%`,
              height: `${z.style.h}%`,
            }}
          >
            {z.label}
          </div>
        ))}
        {Object.entries(NODE_POSITIONS).map(([node, p]) => {
          const isCurrent = node === current;
          const size = isCurrent ? "h-[42px] w-[42px]" : "h-[34px] w-[34px]";
          const bg = isCurrent ? "bg-green" : "bg-[#8aa0b7]";
          const ring = isCurrent
            ? "shadow-[0_0_0_8px_rgba(29,155,117,.16),0_14px_26px_rgba(29,155,117,.28)]"
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
