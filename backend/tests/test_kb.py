"""Knowledge base unit tests (TDD-04): pathfinding, services, check-in, FAQ
(keyword retriever), and the airport-agnostic guarantee via a temp data pack.

KB_RETRIEVER=keyword (conftest) keeps these offline — no model download.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from app.kb import build_knowledge_base
from app.kb import loader
from app.kb.graph import directions, route_summary, shortest_path


@pytest.fixture
def kb():
    return build_knowledge_base()  # keyword retriever (conftest)


# --- graph / directions ----------------------------------------------------

def test_shortest_path_to_concourse(kb):
    pack = kb.pack("AUH")
    path = shortest_path(pack, "entrance", "concourse-b")
    assert path == ["entrance", "check-in", "security", "duty-free", "concourse-b"]
    assert route_summary(pack, path)["distance_m"] == 535  # 90+120+85+240


def test_directions_resolves_gate_code_to_concourse(kb):
    d = kb.directions("AUH", gate="B12")
    assert d["route"][-1] == "concourse-b"
    assert d["route_summary"]["walking_time_min"] >= 1
    assert d["positions"]["concourse-b"] == {"x": 85, "y": 42}
    # A real AirLabs-style gate resolves by its leading letter too.
    assert kb.directions("AUH", gate="C33")["route"][-1] == "concourse-c"
    assert kb.directions("AUH", gate="A1")["route"][-1] == "concourse-a"


def test_directions_from_position(kb):
    d = kb.directions("AUH", gate="D18", from_node="security")
    assert d["route"][0] == "security"
    assert d["route"][-1] == "concourse-d"


def test_directions_origin_equals_target_resets_to_default(kb):
    # A hosted LLM sometimes sets origin == destination; never route to self.
    d = kb.directions("AUH", to_node="concourse-c", from_node="concourse-c")
    assert d["route"][0] == "entrance"
    assert d["route"][-1] == "concourse-c"


def test_directions_unknown_target_is_empty(kb):
    d = kb.directions("AUH", to_node="nowhere")
    assert d["route"] == []
    assert d["route_summary"] is None


# --- services / check-in ---------------------------------------------------

def test_find_service_filter(kb):
    names = [s["name"] for s in kb.find_service("AUH", "pharmacy")["results"]]
    assert names == ["Airport Pharmacy"]


def test_checkin_airline_override_and_default(kb):
    assert "Saudia" in kb.checkin("AUH", "SV")["zone"]
    assert kb.checkin("AUH", "ZZ")["node"] == "check-in"  # falls back to default


# --- faq (keyword retriever) ----------------------------------------------

def test_faq_matches_topic_and_localizes(kb):
    en = kb.faq("AUH", "I lost my luggage", lang="en")
    assert "baggage" in en["sources"][0]
    fr = kb.faq("AUH", "where is the prayer room", lang="fr")
    assert fr["lang"] == "fr"  # answer localized to the requested language


def test_faq_miss_returns_none(kb):
    assert kb.faq("AUH", "zzzz qwerty", lang="en")["answer"] is None


# --- airport-agnostic guarantee -------------------------------------------

def test_second_airport_pack_works(tmp_path, monkeypatch):
    """Drop a brand-new pack under data/<id>/ and everything works, no code change."""
    pack_dir = tmp_path / "TST"
    pack_dir.mkdir()
    (pack_dir / "airport.yaml").write_text("airport_id: TST\ndefault_origin: a\n")
    (pack_dir / "layout.yaml").write_text(
        textwrap.dedent(
            """
            nodes: {a: Alpha, b: Bravo, c: Charlie}
            positions: {a: {x: 0, y: 0}, b: {x: 50, y: 0}, c: {x: 100, y: 0}}
            edges:
              - {a: a, b: b, distance_m: 100}
              - {a: b, b: c, distance_m: 200}
            gate_nodes: {C: c}
            """
        )
    )
    (pack_dir / "services.yaml").write_text("services: []\n")
    (pack_dir / "checkin.yaml").write_text("default: {zone: Desk, node: a}\n")
    (pack_dir / "faq.yaml").write_text(
        "faq:\n  - id: hours\n    topic: hours\n    variants:\n"
        "      en: {question: opening hours, answer: Open all day.}\n"
    )
    monkeypatch.setattr(loader, "DATA_DIR", tmp_path)
    loader.load_pack.cache_clear()

    new_kb = build_knowledge_base()
    d = new_kb.directions("TST", gate="C")
    assert d["route"] == ["a", "b", "c"]
    assert d["route_summary"]["distance_m"] == 300
    assert new_kb.faq("TST", "opening hours", lang="en")["answer"] == "Open all day."
    loader.load_pack.cache_clear()  # don't leak the temp pack to other tests
