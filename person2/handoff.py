"""
Call-Handoff Module — Lossless Context Transfer

Packages a call's full state into a serializable bundle so the receiving
agent's UI is immediately pre-populated with risk bars, SVI, evidence,
timeline, and consent — no blank screen, no data loss.
"""

import json
import datetime
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# These imports are used when the module is called from the merged pipeline
# server.  The test file constructs mock objects directly, so these are
# imported lazily / by reference only.
# ---------------------------------------------------------------------------
try:
    from decision_aid import DecisionAidLayer, ActionType, ActionState
    from consent import ConsentState, ConsentPurpose
except ImportError:
    # Allow the module to be imported standalone for testing with mocks
    pass


@dataclass
class HandoffPackage:
    """Immutable snapshot of a call's full context at the moment of transfer."""

    call_id: str
    timestamp: str                          # ISO-8601
    from_agent_id: str
    to_agent_id: str
    reason: str                             # e.g. "requires legal-aid specialist"

    # Risk assessment state (copied verbatim from pipeline output)
    current_risk_vector: Dict[str, Any]     # {scores, confidence, overall_confidence}
    current_svi: Dict[str, Any]             # {value, bucket}
    matched_evidence: Dict[str, List[str]]  # dimension -> [phrases]

    # Behavioural signals
    silence_events: List[Dict[str, Any]]

    # Case narrative
    case_timeline: List[str]                # timestamped event strings

    # Governance state — snapshots, NOT copies (same call_id continues)
    consent_state: Dict[str, bool]          # purpose -> granted
    action_history: List[Dict[str, str]]    # [{action_type, state}, ...]


# ---------------------------------------------------------------------------
# Factory: gather current state from all existing components
# ---------------------------------------------------------------------------

def create_handoff_package(
    call_id: str,
    from_agent_id: str,
    to_agent_id: str,
    reason: str,
    pipeline_state: dict,
    decision_aid_layer,          # DecisionAidLayer instance
    consent_state,               # ConsentState instance
) -> HandoffPackage:
    """
    Gather the current state from all existing components into one
    serializable package.

    Parameters
    ----------
    pipeline_state : dict
        The latest pipeline output dict, expected to contain at minimum:
        ``risk_vector`` (with ``scores``, ``confidence``, ``matched_evidence``,
        ``overall_confidence``), ``svi`` (with ``value``, ``bucket``),
        ``silence_events``, and optionally ``case_timeline``.
    decision_aid_layer : DecisionAidLayer
        The per-connection decision-aid instance.
    consent_state : ConsentState
        The per-call consent tracker.
    """

    # --- Risk vector & SVI (deep-copy via JSON round-trip for isolation) ---
    risk_vector = json.loads(json.dumps(pipeline_state.get("risk_vector", {})))
    svi = json.loads(json.dumps(pipeline_state.get("svi", {})))
    matched_evidence = json.loads(json.dumps(
        risk_vector.get("matched_evidence",
                        pipeline_state.get("matched_evidence", {}))
    ))
    silence_events = json.loads(json.dumps(
        pipeline_state.get("silence_events", [])
    ))
    case_timeline = list(pipeline_state.get("case_timeline", []))

    # --- Action history from DecisionAidLayer ---------------------------------
    action_history: List[Dict[str, str]] = []
    for (cid, action_type), record in decision_aid_layer.actions.items():
        if cid == call_id:
            action_history.append({
                "action_type": (action_type.value
                                if hasattr(action_type, "value")
                                else str(action_type)),
                "state": (record.state.value
                          if hasattr(record.state, "value")
                          else str(record.state)),
            })

    # --- Consent snapshot -----------------------------------------------------
    consent_snapshot: Dict[str, bool] = {}
    if hasattr(consent_state, "_consents"):
        for purpose, granted in consent_state._consents.items():
            key = purpose.value if hasattr(purpose, "value") else str(purpose)
            consent_snapshot[key] = granted
    elif isinstance(consent_state, dict):
        consent_snapshot = dict(consent_state)

    return HandoffPackage(
        call_id=call_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        reason=reason,
        current_risk_vector=risk_vector,
        current_svi=svi,
        matched_evidence=matched_evidence,
        silence_events=silence_events,
        case_timeline=case_timeline,
        consent_state=consent_snapshot,
        action_history=action_history,
    )


# ---------------------------------------------------------------------------
# Applicator: produce the JSON-ready payload for the new agent's frontend
# ---------------------------------------------------------------------------

def apply_handoff_package(package: HandoffPackage) -> dict:
    """
    Transform a HandoffPackage into a JSON-ready payload that is sent to the
    NEW agent's frontend the moment they pick up the transferred call.

    The ``type`` field is ``"handoff_received"`` so the frontend can
    distinguish it from normal ``transcript_update`` messages and instantly
    pre-populate all panels.
    """
    return {
        "type": "handoff_received",
        "call_id": package.call_id,
        "from_agent": package.from_agent_id,
        "reason": package.reason,
        "risk_vector": package.current_risk_vector,
        "svi": package.current_svi,
        "evidence": package.matched_evidence,
        "timeline": package.case_timeline,
        "consent_summary": package.consent_state,
        "silence_events": package.silence_events,
        "action_history": package.action_history,
    }


# ---------------------------------------------------------------------------
# Convenience: full JSON serialization
# ---------------------------------------------------------------------------

def handoff_to_json(package: HandoffPackage) -> str:
    """Serialize a HandoffPackage to a JSON string."""
    return json.dumps(asdict(package), default=str)


# ---------------------------------------------------------------------------
# Sanity self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from decision_aid import DecisionAidLayer, ActionType
    from consent import ConsentState, ConsentPurpose

    # Set up a mock call
    call_id = "handoff-demo-001"
    aid = DecisionAidLayer()
    aid.suggest_for_bucket(call_id, "critical")
    aid.agent_confirm(call_id, ActionType.counseling_referral, "agent_A", True)

    consent = ConsentState()
    consent.grant(ConsentPurpose.recording)
    consent.grant(ConsentPurpose.ai_analysis)

    pipeline_state = {
        "risk_vector": {
            "scores": {"acute_distress": 0.9, "self_harm_risk": 0.45},
            "confidence": {"acute_distress": 0.98, "self_harm_risk": 0.86},
            "matched_evidence": {"acute_distress": ["scared", "send someone"]},
            "overall_confidence": 0.86,
        },
        "svi": {"value": 82.5, "bucket": "critical"},
        "silence_events": [{"start_sec": 28.1, "duration_sec": 3.5, "placement": "mid_sentence"}],
        "case_timeline": ["00:01 — Call started", "00:28 — Critical risk detected (SVI: 82.5)"],
    }

    pkg = create_handoff_package(
        call_id, "agent_A", "agent_B", "requires legal-aid specialist",
        pipeline_state, aid, consent,
    )
    payload = apply_handoff_package(pkg)

    assert payload["type"] == "handoff_received"
    assert payload["from_agent"] == "agent_A"
    assert payload["risk_vector"]["scores"] == pipeline_state["risk_vector"]["scores"]
    assert payload["svi"] == pipeline_state["svi"]
    assert payload["evidence"] == pipeline_state["risk_vector"]["matched_evidence"]
    assert payload["consent_summary"]["recording"] is True
    assert payload["consent_summary"]["ai_analysis"] is True
    assert len(payload["action_history"]) == 5  # critical suggests all 5

    print("Handoff self-test passed.")
    print("Payload:", json.dumps(payload, indent=2))
