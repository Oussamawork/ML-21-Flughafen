"use client";

import type { FlightInfo } from "@/lib/types";

import { Card, SectionTitle } from "./Card";

// Mirrors SkyGuide's .flight-card (.flight-hero + .details-grid).
interface Props {
  flight: FlightInfo | null;
  checkin: string | null;
  loading: boolean;
  apiOnline: boolean;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <>
      <span className="font-[800] text-muted">{label}</span>
      <strong className="justify-self-end">{value}</strong>
    </>
  );
}

const DASH = "—";

export function FlightCard({ flight, checkin, loading, apiOnline }: Props) {
  const heroNumber = loading ? "Loading…" : flight?.flight_number ?? "—";
  const route = loading
    ? "Updating ticket data"
    : flight
      ? `${flight.departure_airport ?? "—"} → ${flight.arrival_airport ?? "—"}`
      : "Enter a flight number above";

  // Map our /flight payload onto SkyGuide's seven rows.
  const boarding = flight?.estimated || flight?.scheduled || DASH;

  return (
    <Card>
      <SectionTitle title="Flight Information" badge={apiOnline ? "API online" : "API offline"} />
      <div className="mb-3.5 grid gap-[5px] rounded-lg bg-navy p-4 text-white">
        <strong className="text-[28px]">{heroNumber}</strong>
        <span className="text-[#dbe8ff]">{route}</span>
      </div>
      <div className="grid grid-cols-[1fr_auto] gap-x-[18px] gap-y-2.5">
        <Row label="Airline" value={flight?.airline ?? DASH} />
        <Row label="Terminal" value={flight?.terminal ?? DASH} />
        <Row label="Gate" value={flight?.gate ?? DASH} />
        {/* Check-in is KB-sourced (TDD-04), not from the flight API. */}
        <Row label="Check-in" value={flight ? checkin ?? DASH : DASH} />
        <Row label="Baggage" value={flight?.baggage ?? DASH} />
        <Row label="Boarding" value={boarding} />
        <Row label="Status" value={flight?.status ?? DASH} />
      </div>
    </Card>
  );
}
