"""Prompts + multilingual answer composition for the agent (TDD-02).

The hosted LLM providers use `SYSTEM_PROMPT`/`FEW_SHOT`. The offline provider uses
the templates here to compose deterministic, multilingual answers from tool results
so the pipeline runs with zero API keys.
"""

from __future__ import annotations

SYSTEM_PROMPT = (
    "You are a multilingual airport wayfinding assistant for airport {airport_id}. "
    "Ground every answer in the tool results and copy gate, terminal, "
    "baggage, and time values **exactly** as returned — never change, swap, or guess "
    "them. The flight number is a typed field — do not invent it. For wayfinding, call "
    "`directions` and read out the route and walking distance. For places (pharmacy, "
    "lounge, restroom, food, atm) call `find_service`. For general airport questions "
    "call `faq` and cite its sources. Call a tool at most once per flight per turn. If "
    "a lookup fails or a field is missing, say so briefly."
)

# Human-readable language names for the per-turn language lock.
LANG_NAMES = {
    "ar": "Arabic",
    "ary": "Moroccan Darija (written in Arabic script)",
    "fr": "French",
    "en": "English",
}


def system_prompt(airport_id: str, language: str) -> str:
    """System prompt with a strict single-language lock for the hosted LLM.

    Without naming the exact target language, models code-switch (e.g. rendering
    English route-step names into Chinese). Pin the language + forbid mixing."""
    name = LANG_NAMES.get(language, "English")
    lock = (
        f" Respond ENTIRELY in {name} ({language}). Use only this language and its "
        "script — never mix in English, Chinese, or any other language. Translate "
        "route step names into this language; keep only identifiers like gate codes "
        "(e.g. B12) and terminal letters (e.g. A) verbatim."
    )
    return SYSTEM_PROMPT.format(airport_id=airport_id) + lock

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
    "directions": {
        "ar": "اتجه إلى {dest}: {route}. المسافة {distance} متر، حوالي {minutes} دقيقة مشياً.",
        "ary": "سير ل{dest}: {route}. المسافة {distance} متر، تقريباً {minutes} دقيقة بالمشي.",
        "fr": "Dirigez-vous vers {dest} : {route}. Distance {distance} m, environ {minutes} min à pied.",
        "en": "Head to {dest}: {route}. Distance {distance} m, about {minutes} min walk.",
    },
    "no_route": {
        "ar": "لم أتمكن من إيجاد مسار. حدّد وجهتك أو رقم رحلتك من فضلك.",
        "ary": "مالقيتش الطريق. حدّد فين باغي تمشي ولا عطيني رقم الرحلة عافاك.",
        "fr": "Je n'ai pas pu trouver d'itinéraire. Précisez votre destination ou votre vol.",
        "en": "I couldn't find a route. Please tell me your destination or flight number.",
    },
    "service": {
        "ar": "إليك ما وجدت: {results}.",
        "ary": "ها اللي لقيت: {results}.",
        "fr": "Voici ce que j'ai trouvé : {results}.",
        "en": "Here's what I found: {results}.",
    },
    "no_service": {
        "ar": "لم أجد هذه الخدمة هنا.",
        "ary": "مالقيتش هاد الخدمة هنا.",
        "fr": "Je n'ai pas trouvé ce service ici.",
        "en": "I couldn't find that service here.",
    },
    "no_answer": {
        "ar": "ليس لدي معلومات كافية عن ذلك. حاول صياغة سؤالك بشكل آخر.",
        "ary": "ماعنديش معلومات كافية على هادشي. عاود صيغ السؤال عافاك.",
        "fr": "Je n'ai pas assez d'informations là-dessus. Reformulez votre question.",
        "en": "I don't have enough information on that. Try rephrasing your question.",
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


def compose_directions(result: dict | None, lang: str) -> str:
    """Render a `directions` tool result into a route answer in `lang`."""
    route = (result or {}).get("route") or []
    if not route:
        return template("no_route", lang)
    steps = (result or {}).get("steps") or route
    summary = (result or {}).get("route_summary") or {}
    return template("directions", lang).format(
        dest=steps[-1],
        route=" → ".join(steps),
        distance=summary.get("distance_m", 0),
        minutes=summary.get("walking_time_min", 0),
    )


def compose_service(result: dict | None, lang: str) -> str:
    """Render a `find_service` tool result into an answer in `lang`."""
    results = (result or {}).get("results") or []
    if not results:
        return template("no_service", lang)
    items = ", ".join(
        f"{s.get('name')} ({s.get('zone')}, {s.get('hours')})" for s in results[:4]
    )
    return template("service", lang).format(results=items)


def compose_faq(result: dict | None, lang: str) -> str:
    """Return the FAQ answer (already in the user's language) or a graceful miss."""
    answer = (result or {}).get("answer")
    return answer or template("no_answer", lang)
