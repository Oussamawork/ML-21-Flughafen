"""/map endpoint tests (TDD-04/06). Mock flight provider + keyword retriever."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_map_layout_only():
    with TestClient(app) as c:
        r = c.post("/map", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["airport_id"] == "AUH"
    assert "gate-b12" in body["nodes"]
    assert body["positions"]["entrance"] == {"x": 8, "y": 54}
    assert body["zones"]  # labelled rectangles present
    assert body["route"] == []  # no target -> shell only


def test_map_route_for_flight():
    with TestClient(app) as c:
        r = c.post("/map", json={"flight_number": "SV624"})
    assert r.status_code == 200
    body = r.json()
    assert body["route"][-1] == "gate-b12"
    assert body["route_summary"]["distance_m"] == 525
    assert body["current_position"] == "entrance"


def test_map_route_from_position_to_gate():
    with TestClient(app) as c:
        r = c.post("/map", json={"gate": "D18", "position": "pharmacy"})
    assert r.status_code == 200
    body = r.json()
    assert body["route"][0] == "pharmacy"
    assert body["route"][-1] == "gate-d18"


def test_map_to_node_overrides_flight_gate():
    # The passenger explores: ticket is SV624 (gate B12) but they pick gate D18.
    with TestClient(app) as c:
        r = c.post("/map", json={"flight_number": "SV624", "to_node": "gate-d18", "position": "pharmacy"})
    assert r.status_code == 200
    body = r.json()
    assert body["to_node"] == "gate-d18"  # explicit destination wins over the gate
    assert body["route"][0] == "pharmacy"
    assert body["route"][-1] == "gate-d18"


def test_map_unknown_airport_404():
    with TestClient(app) as c:
        r = c.post("/map", json={"airport_id": "XXX"})
    assert r.status_code == 404
