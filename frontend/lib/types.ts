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

export interface FlightResponse {
  flight: FlightInfo;
  route: Record<string, unknown> | null; // reserved for the KB map (TDD-04)
}

// UI-side chat message model.
export interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  language?: Language;
  intent?: string;
  toolTrace?: ToolCall[];
  audioUrl?: string; // absolute URL to a playable clip
  latencyMs?: Record<string, number>;
}
