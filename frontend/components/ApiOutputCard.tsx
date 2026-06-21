"use client";

import { Card, SectionTitle } from "./Card";

// Mirrors SkyGuide's .api-card (structured JSON proof).
interface Props {
  payload: unknown;
}

export function ApiOutputCard({ payload }: Props) {
  const text = payload
    ? JSON.stringify(payload, null, 2)
    : "Waiting for flight...";
  return (
    <Card>
      <SectionTitle title="Structured API Output" badge="Report proof" />
      <pre className="m-0 max-h-[340px] min-h-[250px] overflow-auto whitespace-pre-wrap rounded-lg bg-navy p-3.5 text-xs leading-[1.55] text-[#e7f0ff]">
        {text}
      </pre>
    </Card>
  );
}
