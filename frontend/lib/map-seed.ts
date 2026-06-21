// AUH map seed — the pre-fetch / offline fallback shell for the map card. The
// live layout (positions, zones, route) comes from the KB-driven /map endpoint
// (TDD-04); this mirrors backend/app/kb/data/AUH/layout.yaml so the shell matches.

export interface Point {
  x: number;
  y: number;
}

export const NODE_POSITIONS: Record<string, Point> = {
  entrance: { x: 7, y: 55 },
  "check-in": { x: 20, y: 55 },
  security: { x: 33, y: 55 },
  "duty-free": { x: 47, y: 55 },
  baggage: { x: 33, y: 26 },
  "concourse-a": { x: 73, y: 20 },
  "concourse-b": { x: 85, y: 42 },
  "concourse-c": { x: 85, y: 66 },
  "concourse-d": { x: 73, y: 88 },
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
