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
    assert "concourse-b" in body["nodes"]
    assert body["positions"]["entrance"] == {"x": 38, "y": 35}
    assert body["zones"]  # labelled rectangles present
    assert body["route"] == []  # no target -> shell only


def test_map_route_for_flight():
    with TestClient(app) as c:
        r = c.post("/map", json={"flight_number": "SV624"})
    assert r.status_code == 200
    body = r.json()
    assert body["route"][-1] == "concourse-b"  # gate B12 -> concourse B
    assert body["route_summary"]["distance_m"] == 535
    assert body["current_position"] == "entrance"
    assert body["gate_label"] == "B12"  # real gate code labelled at the concourse


def test_map_route_from_position_to_gate():
    with TestClient(app) as c:
        r = c.post("/map", json={"gate": "D18", "position": "security"})
    assert r.status_code == 200
    body = r.json()
    assert body["route"][0] == "security"
    assert body["route"][-1] == "concourse-d"


def test_map_to_node_overrides_flight_gate():
    # The passenger explores: ticket is SV624 (gate B12) but they pick concourse D.
    with TestClient(app) as c:
        r = c.post("/map", json={"flight_number": "SV624", "to_node": "concourse-d", "position": "security"})
    assert r.status_code == 200
    body = r.json()
    assert body["to_node"] == "concourse-d"  # explicit destination wins over the gate
    assert body["route"][0] == "security"
    assert body["route"][-1] == "concourse-d"


def test_map_unknown_airport_404():
    with TestClient(app) as c:
        r = c.post("/map", json={"airport_id": "XXX"})
    assert r.status_code == 404
