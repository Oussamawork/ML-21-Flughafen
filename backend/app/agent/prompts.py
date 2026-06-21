"""Prompts + multilingual answer composition for the agent (TDD-02).

The hosted LLM providers use `SYSTEM_PROMPT`/`FEW_SHOT`. The offline provider uses
the templates here to compose deterministic, multilingual answers from tool results
so the pipeline runs with zero API keys.
"""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You are a multilingual airport wayfinding assistant for airport {airport_id}. "
    "Reply in the user's language (Arabic `ar`, Darija `ary`, French `fr`, or "
    "English `en`). Use the provided tools to ground answers in live flight data; "
    "never invent gates, terminals, or times. The flight number is a typed field — "
    "do not guess it. If a lookup fails, say so briefly and offer to help otherwise."
)

# A Darija example mirroring the proposal ("ayna bawwabati, rihlati SV-624").
FEW_SHOT = [
    {"role": "user", "content": "فين البّاب ديالي، الرحلة SV624؟"},
    {"role": "assistant", "content": "البّاب ديالك هو B12، تيرمينال A."},
]

# Templated answers per detected language (ar | ary | fr | en).
_TEMPLATES = {
    "gate": {
        "ar": "بوابتك هي {gate}، المبنى {terminal}. الوقت {time}.",
        "ary": "البّاب ديالك هو {gate}، تيرمينال {terminal}. الوقت {time}.",
        "fr": "Votre porte est {gate}, terminal {terminal}. Heure {time}.",
        "en": "Your gate is {gate}, terminal {terminal}. Time {time}.",
    },
    "unknown_flight": {
        "ar": "لم أجد معلومات عن هذه الرحلة. تأكد من رقم الرحلة من فضلك.",
        "ary": "مالقيتش معلومات على هاد الرحلة. عافاك تأكد من الرقم.",
        "fr": "Je n'ai pas trouvé ce vol. Vérifiez le numéro, s'il vous plaît.",
        "en": "I couldn't find that flight. Please check the flight number.",
    },
    "flight_unavailable": {
        "ar": "خدمة بيانات الرحلات غير متوفرة حالياً. حاول مرة أخرى بعد قليل.",
        "ary": "خدمة الرحلات ماخدّامة دابا. عاود من بعد عافاك.",
        "fr": "Les données de vol sont indisponibles pour l'instant. Réessayez bientôt.",
        "en": "Flight data is unavailable right now. Please try again shortly.",
    },
    "fallback": {
        "ar": "أنا مساعد المطار. يمكنني مساعدتك في البوابات والرحلات والخدمات.",
        "ary": "أنا مساعد ديال المطار. نقدر نعاونك فالبيبان والرحلات والخدمات.",
        "fr": "Je suis l'assistant de l'aéroport. Je peux aider pour les portes, vols et services.",
        "en": "I'm the airport assistant. I can help with gates, flights and services.",
    },
}


def template(key: str, lang: str) -> str:
    """Language-specific template string, falling back to English."""
    return _TEMPLATES[key].get(lang, _TEMPLATES[key]["en"])


def compose_flight_answer(info: dict | None, lang: str) -> str:
    """Render a flight lookup result into an answer in `lang`.

    `info` is the canonical flight dict (services/flight.py) or None/empty/error.
    The canonical schema has no `boarding`; the time slot uses estimated|scheduled.
    """
    if not info or info.get("error"):
        key = "flight_unavailable" if (info or {}).get("error") else "unknown_flight"
        return template(key, lang)
    time = info.get("estimated") or info.get("scheduled") or "—"
    return template("gate", lang).format(
        gate=info.get("gate") or "—",
        terminal=info.get("terminal") or "—",
        time=time,
    )
