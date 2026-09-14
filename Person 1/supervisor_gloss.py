"""
Supervisor Gloss — Approximate English translation for supervisor readability ONLY.

This module produces a rough English gloss of the caller's original-language
transcript.  The output is NEVER fed into risk_scorer.py or any scoring
function.  It exists solely so that a supervisor who may not speak the
caller's language can follow the conversation at a high level.
"""


def generate_gloss(original_text: str, source_lang: str) -> str:
    """
    Produce an approximate English gloss of *original_text*.

    Parameters
    ----------
    original_text : str
        The caller's transcript in its original spoken language.
    source_lang : str
        ISO-639 language code detected by ASR (e.g. "hi", "en", "hinglish").

    Returns
    -------
    str
        An English gloss string.  If the text is already English, it is
        returned as-is.  If no translation capability is available in this
        environment, a clearly-labelled stub is returned so the full data
        flow can still be built and tested end-to-end.
    """
    cleaned = original_text.strip()
    if not cleaned:
        return ""

    # If the source language is already English, no translation is needed.
    if source_lang in ("en", "english"):
        return cleaned

    # ------------------------------------------------------------------
    # In a production environment this would call a lightweight MT library
    # (e.g. Argos Translate, ctranslate2, or an LLM endpoint).
    #
    # Since no translation capability is available in this environment we
    # return a clearly-labelled stub so the interface and data flow can
    # still be built and tested end-to-end.
    # ------------------------------------------------------------------
    return f"[gloss unavailable: {cleaned}]"
