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
