// AUH map seed — the pre-fetch / offline fallback shell for the map card. The
// live layout (positions, zones, route) comes from the KB-driven /map endpoint
// (TDD-04); this mirrors backend/app/kb/data/AUH/layout.yaml so the shell matches.

export interface Point {
  x: number;
  y: number;
}

// % coords over the real AUH map backdrop (mirrors layout.yaml positions).
export const NODE_POSITIONS: Record<string, Point> = {
  entrance: { x: 38, y: 35 },
  "check-in": { x: 45, y: 40 },
  security: { x: 50, y: 43 },
  "duty-free": { x: 54, y: 46 },
  baggage: { x: 49, y: 51 },
  "concourse-a": { x: 20, y: 55 },
  "concourse-b": { x: 58, y: 79 },
  "concourse-c": { x: 84, y: 47 },
  "concourse-d": { x: 45, y: 11 },
};

// Zone boxes (mirror layout.yaml zones): %-based layout.
export const ZONES: { label: string; style: Point & { w: number; h: number } }[] = [
  { label: "Entrance", style: { x: 2, y: 46, w: 12, h: 18 } },
  { label: "Check-in", style: { x: 15, y: 43, w: 13, h: 24 } },
  { label: "Security", style: { x: 29, y: 43, w: 11, h: 24 } },
  { label: "Retail Plaza", style: { x: 41, y: 41, w: 15, h: 28 } },
  { label: "Baggage Reclaim", style: { x: 22, y: 15, w: 24, h: 20 } },
  { label: "Concourses", style: { x: 64, y: 12, w: 32, h: 80 } },
];

// Short marker label (concourse-c -> "C", entrance -> "You" handled by caller).
export function shortNode(node: string): string {
  if (node === "entrance") return "You";
  if (node === "check-in") return "CI";
  if (node === "security") return "SEC";
  if (node === "duty-free") return "DF";
  if (node === "baggage") return "BAG";
  if (node.startsWith("concourse-")) return node.split("-")[1].toUpperCase();
  return "•";
}
