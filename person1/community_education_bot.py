"""
Community Education Bot — standalone, low-stakes FAQ chatbot.

Reuses NHAA's multilingual language handling but has NO connection to:
  • risk scoring / SVI computation
  • case file creation or audit logging
  • conversation history storage beyond the current session

This is intentionally the lowest-data-retention part of the system.
"""

import os
import json
import re

# ──────────────────────────────────────────────────────────────────────
# Paths — resolved relative to this file so tests work from any CWD
# ──────────────────────────────────────────────────────────────────────
_DIR = os.path.dirname(os.path.abspath(__file__))
_TOPICS_PATH = os.path.join(_DIR, "education_topics.json")
_KEYWORDS_DIR = os.path.join(_DIR, "keywords")


# ──────────────────────────────────────────────────────────────────────
# Language detection — simple heuristic matching the codebase pattern
# ──────────────────────────────────────────────────────────────────────
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def detect_language(text: str) -> str:
    """
    Lightweight language detector (Hindi / English / Hinglish).

    Uses the same heuristic strategy as the rest of the NHAA codebase:
    presence of Devanagari script indicates Hindi; a mix of Devanagari
    and Latin indicates Hinglish; otherwise English.
    """
    has_devanagari = bool(_DEVANAGARI_RE.search(text))
    has_latin = bool(re.search(r"[a-zA-Z]", text))

    if has_devanagari and has_latin:
        return "hinglish"
    if has_devanagari:
        return "hi"
    return "en"


# ──────────────────────────────────────────────────────────────────────
# Crisis-language detector
# ──────────────────────────────────────────────────────────────────────
def _load_crisis_phrases() -> list[str]:
    """
    Load a minimal subset of first-person distress indicators from the
    existing acute_distress.json and self_harm_risk.json keyword files.

    Only phrases that indicate *first-person* crisis disclosures are
    included — general informational phrases are excluded.
    """
    phrases: list[str] = []
    for filename in ("self_harm_risk.json", "acute_distress.json"):
        filepath = os.path.join(_KEYWORDS_DIR, filename)
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            entries = json.load(f)
        for entry in entries:
            phrases.append(entry["phrase"].lower())
    return phrases


_CRISIS_PHRASES: list[str] = _load_crisis_phrases()


def crisis_language_detector(text: str) -> bool:
    """
    Check whether *text* contains a first-person distress indicator.

    Returns True if any phrase from acute_distress.json or
    self_harm_risk.json appears as a substring (case-insensitive).
    A True result means the bot must IMMEDIATELY stop normal FAQ
    responses and hand off to 14566.
    """
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in _CRISIS_PHRASES)


# ──────────────────────────────────────────────────────────────────────
# Crisis hand-off messages (trilingual)
# ──────────────────────────────────────────────────────────────────────
_CRISIS_HANDOFF = {
    "en": (
        "It sounds like you may be going through something very difficult "
        "right now. This chatbot is not equipped to provide the support you "
        "need. Please call 14566 (NHAA Helpline) immediately — trained "
        "counselors are available 24/7, and the call is free and "
        "confidential. You are not alone. 💛"
    ),
    "hi": (
        "ऐसा लगता है कि आप अभी बहुत कठिन दौर से गुज़र रहे हैं। यह चैटबॉट "
        "आपको ज़रूरी सहायता देने में सक्षम नहीं है। कृपया तुरंत 14566 "
        "(NHAA हेल्पलाइन) पर कॉल करें — प्रशिक्षित काउंसलर 24/7 उपलब्ध हैं, "
        "और कॉल मुफ्त और गोपनीय है। आप अकेले नहीं हैं। 💛"
    ),
    "hinglish": (
        "Lagta hai aap abhi bahut mushkil waqt se guzar rahe hain. Yeh "
        "chatbot aapko zaruri support dene mein saksham nahi hai. Please "
        "turant 14566 (NHAA Helpline) par call karein — trained counselors "
        "24/7 available hain, aur call free aur confidential hai. Aap akele "
        "nahi hain. 💛"
    ),
}

_FALLBACK_RESPONSE = {
    "en": (
        "I'm sorry, I couldn't find a specific answer for that. For "
        "immediate help or questions I can't answer, please call 14566 "
        "(NHAA Helpline) — it's free, confidential, and available 24/7."
    ),
    "hi": (
        "क्षमा करें, मुझे इसका कोई विशिष्ट उत्तर नहीं मिला। तत्काल सहायता "
        "या ऐसे प्रश्नों के लिए जिनका उत्तर मैं नहीं दे सकती, कृपया 14566 "
        "(NHAA हेल्पलाइन) पर कॉल करें — यह मुफ्त, गोपनीय और 24/7 उपलब्ध है।"
    ),
    "hinglish": (
        "Sorry, mujhe iska koi specific answer nahi mila. Immediate help ya "
        "aise questions ke liye jinke answer main nahi de sakti, please 14566 "
        "(NHAA Helpline) par call karein — yeh free, confidential aur 24/7 "
        "available hai."
    ),
}


# ──────────────────────────────────────────────────────────────────────
# CommunityEducationBot
# ──────────────────────────────────────────────────────────────────────
class CommunityEducationBot:
    """
    Standalone FAQ chatbot for community education.

    Deliberately carries:
      • NO risk scoring
      • NO SVI computation
      • NO audit logging
      • NO case-file creation
      • NO conversation history beyond the current session
    """

    def __init__(self, topics_path: str | None = None):
        path = topics_path or _TOPICS_PATH
        with open(path, "r", encoding="utf-8") as f:
            self.topics: list[dict] = json.load(f)

        # Pre-compute lowercased trigger phrases for faster matching
        for topic in self.topics:
            topic["_triggers_lower"] = [
                p.lower() for p in topic["trigger_phrases"]
            ]

        # Session-level crisis flag: once tripped, stays tripped
        self._crisis_triggered = False

    # ── public API ────────────────────────────────────────────────────

    def respond(self, user_text: str) -> dict:
        """
        Process *user_text* and return a response dict.

        Returns
        -------
        dict with keys:
            matched_intent : str   — intent id, "crisis_redirect", or "fallback"
            response       : str   — the response text in the detected language
            language       : str   — "en", "hi", or "hinglish"
        """
        language = detect_language(user_text)

        # ── Crisis check (highest priority, sticky per session) ───────
        if self._crisis_triggered or crisis_language_detector(user_text):
            self._crisis_triggered = True
            return {
                "matched_intent": "crisis_redirect",
                "response": _CRISIS_HANDOFF.get(language, _CRISIS_HANDOFF["en"]),
                "language": language,
            }

        # ── Intent matching ───────────────────────────────────────────
        text_lower = user_text.lower()
        best_match = None
        best_score = 0

        for topic in self.topics:
            for trigger in topic["_triggers_lower"]:
                if trigger in text_lower:
                    score = len(trigger)  # longer match = more specific
                    if score > best_score:
                        best_score = score
                        best_match = topic

        if best_match is not None:
            response_text = best_match["response"].get(
                language, best_match["response"]["en"]
            )
            return {
                "matched_intent": best_match["intent"],
                "response": response_text,
                "language": language,
            }

        # ── Fallback ──────────────────────────────────────────────────
        return {
            "matched_intent": "fallback",
            "response": _FALLBACK_RESPONSE.get(language, _FALLBACK_RESPONSE["en"]),
            "language": language,
        }
