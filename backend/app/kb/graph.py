"""Airport-map pathfinding (TDD-04 §6). Ported from SkyGuide's BFS + edge-distance
table: shortest path over the layout graph, enriched with per-step + total walking
distance and an estimated walking time. Returns the route as map nodes + positions
so the frontend can draw the polyline (TDD-07).
"""

from __future__ import annotations

from collections import deque

from .loader import Pack


def shortest_path(pack: Pack, start: str, end: str) -> list[str]:
    """BFS shortest node path start->end (the layout is a near-tree, so fewest
    hops == shortest distance). Empty list if either node is unknown/unreachable."""
    adj = pack.adjacency
    if start not in adj or end not in pack.node_names:
        return []
    if start == end:
        return [start]
    queue: deque[tuple[str, list[str]]] = deque([(start, [start])])
    seen = {start}
    while queue:
        node, path = queue.popleft()
        for nxt, _ in adj.get(node, []):
            if nxt in seen:
                continue
            if nxt == end:
                return path + [nxt]
            seen.add(nxt)
            queue.append((nxt, path + [nxt]))
    return []


def _edge_distance(pack: Pack, a: str, b: str) -> int:
    for nxt, dist in pack.adjacency.get(a, []):
        if nxt == b:
            return dist
    return 95  # sensible default for an unlabelled edge (matches SkyGuide)


def route_summary(pack: Pack, path: list[str]) -> dict:
    total = sum(_edge_distance(pack, path[i], path[i + 1]) for i in range(len(path) - 1))
    speed = pack.layout.get("walking_speed_m_per_min", 75) or 75
    return {
        "distance_m": total,
        "walking_time_min": max(1, round(total / speed)) if total else 0,
        "steps": max(0, len(path) - 1),
    }


def directions(pack: Pack, from_node: str, to_node: str) -> dict:
    """Route between two layout nodes. Returns the shape the agent tool + /map +
    the frontend renderer expect: steps, route nodes, positions, summary."""
    path = shortest_path(pack, from_node, to_node)
    names = pack.node_names
    steps = [names.get(n, n) for n in path]
    positions = {n: pack.positions[n] for n in path if n in pack.positions}
    return {
        "from_node": from_node,
        "to_node": to_node,
        "route": path,
        "steps": steps,
        "positions": positions,
        "route_summary": route_summary(pack, path) if path else None,
    }
