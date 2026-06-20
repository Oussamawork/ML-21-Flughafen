"""Tiny language detector shared by the stubs (TDD-00: language is first-class).

Heuristic only — good enough for the stub/demo. The real agent (TDD-02) will use
a proper language-ID model. Returns one of: ar, ary (Darija), fr, en.
"""

from __future__ import annotations

import re

_ARABIC = re.compile(r"[؀-ۿ]")
# A few common Darija (Latin/Arabizi) and French markers for the heuristic.
_DARIJA_HINTS = {
    "fin",
    "bghit",
    "wach",
    "chhal",
    "bawwabati",
    "rihlati",
    "dyali",
    "kayn",
}
_FRENCH_HINTS = {
    "où",
    "ou",
    "est",
    "la",
    "le",
    "porte",
    "vol",
    "proche",
    "bonjour",
    "merci",
}


def detect_language(text: str) -> str:
    lowered = text.lower()
    words = set(re.findall(r"[a-zàâçéèêëîïôûùüÿñæœ]+", lowered))

    if _ARABIC.search(text):
        # Arabic script: could be MSA or Darija; the stub reports "ar".
        return "ar"
    if words & _DARIJA_HINTS:
        return "ary"
    if words & _FRENCH_HINTS:
        return "fr"
    return "en"
