// TypeScript mirrors of the backend (TDD-06) response contracts.

export type Language = "ar" | "ary" | "fr" | "en";

export interface ToolCall {
  tool: string;
  args: Record<string, unknown>;
  result: Record<string, unknown> | null;
}

export interface ChatResponse {
  answer: string;
  language: Language;
  intent: string;
  tool_trace: ToolCall[];
  session_id: string;
  latency_ms: Record<string, number>;
}

export interface ConverseResponse {
  text_in: string;
  answer: string;
  language: Language;
  intent: string;
  audio_url: string;
  session_id: string;
  tool_trace: ToolCall[];
  latency_ms: Record<string, number>;
}

export interface AirportsResponse {
  airports: string[];
  default: string;
}

// Flight lookup (TDD-03 `/flight`). The flight number is typed by the user
// (R1: structured input, not parsed from audio); all fields may be null.
export interface FlightInfo {
  flight_number: string;
  airline: string | null;
  status: string | null;
  direction: string | null; // departure | arrival | other
  scheduled: string | null;
  estimated: string | null;
  actual: string | null;
  gate: string | null;
  terminal: string | null;
  baggage: string | null; // arrivals only
  delay_minutes: number | null;
  departure_airport: string | null;
  arrival_airport: string | null;
  aircraft: string | null;
  source: string;
}

export interface RouteSummary {
  distance_m: number;
  walking_time_min: number;
  steps: number;
}

export interface FlightResponse {
  flight: FlightInfo;
  route: Record<string, unknown> | null; // KB route to the gate (TDD-04)
  checkin: { zone?: string; node?: string } | null; // KB check-in (TDD-04)
}

// Airport map (TDD-04 `/map`): layout + an optional route polyline.
export interface MapResponse {
  airport_id: string;
  nodes: Record<string, string>;
  positions: Record<string, { x: number; y: number }>;
  zones: { label: string; x: number; y: number; w: number; h: number }[];
  route: string[];
  route_summary: RouteSummary | null;
  current_position: string | null;
  to_node: string | null;
  gate_label: string | null;
}
