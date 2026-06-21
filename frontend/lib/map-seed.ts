// Temporary AUH map seed (transcribed from SkyGuide's data/airport_map.json).
// Renders the map shell until the KB-driven /map endpoint lands (TDD-04) — at
// which point positions/zones become airport-agnostic, keyed by airport_id.

export interface Point {
  x: number;
  y: number;
}

export const NODE_POSITIONS: Record<string, Point> = {
  entrance: { x: 8, y: 54 },
  "check-in": { x: 21, y: 54 },
  security: { x: 36, y: 54 },
  "duty-free": { x: 51, y: 54 },
  pharmacy: { x: 39, y: 75 },
  "baggage-03": { x: 32, y: 30 },
  "baggage-06": { x: 40, y: 30 },
  "baggage-11": { x: 48, y: 30 },
  "baggage-14": { x: 56, y: 30 },
  "gate-a03": { x: 72, y: 24 },
  "gate-b12": { x: 78, y: 43 },
  "gate-c07": { x: 78, y: 64 },
  "gate-d18": { x: 72, y: 82 },
};

// Zone boxes (mirrors .zone-* rules in SkyGuide styles.css): %-based layout.
export const ZONES: { label: string; style: Point & { w: number; h: number } }[] = [
  { label: "Entrance", style: { x: 3, y: 44, w: 13, h: 18 } },
  { label: "Check-in", style: { x: 17, y: 40, w: 15, h: 26 } },
  { label: "Security", style: { x: 33, y: 40, w: 12, h: 26 } },
  { label: "Duty free", style: { x: 47, y: 36, w: 17, h: 34 } },
  { label: "Baggage", style: { x: 28, y: 17, w: 34, h: 20 } },
  { label: "Gates", style: { x: 68, y: 14, w: 24, h: 74 } },
];

// Short marker label (mirrors shortNode() in SkyGuide app.js).
export function shortNode(node: string): string {
  if (node === "entrance") return "You";
  if (node === "check-in") return "CI";
  if (node === "security") return "SEC";
  if (node === "duty-free") return "DF";
  if (node === "pharmacy") return "RX";
  if (node.startsWith("baggage")) return "B";
  if (node.startsWith("gate")) return node.split("-")[1].toUpperCase();
  return "•";
}
