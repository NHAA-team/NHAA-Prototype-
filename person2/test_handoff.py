"""
Test: Call-handoff lossless context transfer.

(a) Simulates a call reaching Critical bucket with two matched evidence
    phrases and one silence event, creates a handoff package, applies it,
    and confirms the resulting payload contains the exact same risk vector,
    SVI, and evidence — byte for byte — as the original call's state.

(b) Confirms the fallback works when calibration data is insufficient
    (consent state, action history integrity).
"""

import json
import unittest

from decision_aid import DecisionAidLayer, ActionType, ActionState
from consent import ConsentState, ConsentPurpose
from handoff import HandoffPackage, create_handoff_package, apply_handoff_package


class TestHandoffLosslessTransfer(unittest.TestCase):
    """
    Simulates a Critical-bucket call and proves the handoff payload is
    byte-for-byte identical to the original state.
    """

    def setUp(self):
        """Set up a realistic Critical-bucket call scenario."""
        self.call_id = "test-call-critical-001"

        # --- Risk pipeline output (the "ground truth" state) ---
        self.original_risk_vector = {
            "scores": {
                "acute_distress": 0.90,
                "depression": 0.75,
                "self_harm_risk": 0.45,
                "fear_of_retaliation": 0.95,
                "intimidation": 0.95,
                "dissociation": 0.80,
                "social_isolation": 0.80,
                "chronic_trauma_indicators": 0.75,
            },
            "confidence": {
                "acute_distress": 0.98,
                "depression": 0.95,
                "self_harm_risk": 0.86,
                "fear_of_retaliation": 0.99,
                "intimidation": 0.99,
                "dissociation": 0.91,
                "social_isolation": 0.94,
                "chronic_trauma_indicators": 0.97,
            },
            "matched_evidence": {
                "acute_distress": ["scared", "send someone immediately"],
                "depression": ["completely hopeless"],
            },
            "overall_confidence": 0.86,
        }

        self.original_svi = {"value": 82.5, "bucket": "critical"}

        self.original_silence_events = [
            {"start_sec": 28.1, "duration_sec": 3.5, "placement": "mid_sentence"}
        ]

        self.original_timeline = [
            "00:01 — Call started",
            "00:15 — High risk distress detected (SVI: 55.2)",
            "00:28 — Critical risk detected (SVI: 82.5)",
        ]

        self.pipeline_state = {
            "risk_vector": self.original_risk_vector,
            "svi": self.original_svi,
            "silence_events": self.original_silence_events,
            "case_timeline": self.original_timeline,
        }

        # --- DecisionAidLayer with actions for this call ---
        self.decision_aid = DecisionAidLayer()
        self.decision_aid.suggest_for_bucket(self.call_id, "critical")
        # Agent confirms counseling_referral (non-senior → executed)
        self.decision_aid.agent_confirm(
            self.call_id, ActionType.counseling_referral, "agent_A", True
        )

        # --- ConsentState ---
        self.consent = ConsentState()
        self.consent.grant(ConsentPurpose.recording)
        self.consent.grant(ConsentPurpose.ai_analysis)
        # data_for_improvement left as False (declined by default)

    def test_risk_vector_byte_for_byte_identical(self):
        """The handoff payload's risk_vector must be identical to the original."""
        pkg = create_handoff_package(
            self.call_id, "agent_A", "agent_B",
            "requires legal-aid specialist",
            self.pipeline_state, self.decision_aid, self.consent,
        )
        payload = apply_handoff_package(pkg)

        # Byte-for-byte comparison via canonical JSON serialization
        original_json = json.dumps(self.original_risk_vector, sort_keys=True)
        payload_json = json.dumps(payload["risk_vector"], sort_keys=True)
        self.assertEqual(
            original_json, payload_json,
            "Risk vector must be byte-for-byte identical after handoff"
        )

    def test_svi_byte_for_byte_identical(self):
        """The handoff payload's SVI must be identical to the original."""
        pkg = create_handoff_package(
            self.call_id, "agent_A", "agent_B",
            "requires legal-aid specialist",
            self.pipeline_state, self.decision_aid, self.consent,
        )
        payload = apply_handoff_package(pkg)

        original_json = json.dumps(self.original_svi, sort_keys=True)
        payload_json = json.dumps(payload["svi"], sort_keys=True)
        self.assertEqual(
            original_json, payload_json,
            "SVI must be byte-for-byte identical after handoff"
        )

    def test_evidence_byte_for_byte_identical(self):
        """The handoff payload's evidence must be identical to the original."""
        pkg = create_handoff_package(
            self.call_id, "agent_A", "agent_B",
            "requires legal-aid specialist",
            self.pipeline_state, self.decision_aid, self.consent,
        )
        payload = apply_handoff_package(pkg)

        original_evidence = self.original_risk_vector["matched_evidence"]
        original_json = json.dumps(original_evidence, sort_keys=True)
        payload_json = json.dumps(payload["evidence"], sort_keys=True)
        self.assertEqual(
            original_json, payload_json,
            "Matched evidence must be byte-for-byte identical after handoff"
        )

    def test_silence_events_preserved(self):
        """Silence events must survive the handoff intact."""
        pkg = create_handoff_package(
            self.call_id, "agent_A", "agent_B",
            "requires legal-aid specialist",
            self.pipeline_state, self.decision_aid, self.consent,
        )
        payload = apply_handoff_package(pkg)

        self.assertEqual(len(payload["silence_events"]), 1)
        evt = payload["silence_events"][0]
        self.assertAlmostEqual(evt["start_sec"], 28.1)
        self.assertAlmostEqual(evt["duration_sec"], 3.5)
        self.assertEqual(evt["placement"], "mid_sentence")

    def test_payload_shape_and_type(self):
        """The payload must have type='handoff_received' and all required keys."""
        pkg = create_handoff_package(
            self.call_id, "agent_A", "agent_B",
            "requires legal-aid specialist",
            self.pipeline_state, self.decision_aid, self.consent,
        )
        payload = apply_handoff_package(pkg)

        self.assertEqual(payload["type"], "handoff_received")
        self.assertEqual(payload["from_agent"], "agent_A")
        self.assertEqual(payload["reason"], "requires legal-aid specialist")

        required_keys = {
            "type", "call_id", "from_agent", "reason", "risk_vector",
            "svi", "evidence", "timeline", "consent_summary",
            "silence_events", "action_history",
        }
        self.assertTrue(required_keys.issubset(payload.keys()),
                        f"Missing keys: {required_keys - payload.keys()}")

    def test_action_history_captured(self):
        """All actions for this call_id must appear in the handoff."""
        pkg = create_handoff_package(
            self.call_id, "agent_A", "agent_B",
            "requires legal-aid specialist",
            self.pipeline_state, self.decision_aid, self.consent,
        )
        payload = apply_handoff_package(pkg)

        # Critical bucket suggests all 5 action types
        self.assertEqual(len(payload["action_history"]), 5)

        action_types = {a["action_type"] for a in payload["action_history"]}
        expected_types = {
            "counseling_referral", "legal_aid", "police_intervention",
            "witness_protection", "emergency_escalation",
        }
        self.assertEqual(action_types, expected_types)

        # counseling_referral was agent-confirmed (non-senior) → executed
        counseling = next(
            a for a in payload["action_history"]
            if a["action_type"] == "counseling_referral"
        )
        self.assertEqual(counseling["state"], "executed")

    def test_consent_state_captured(self):
        """Consent snapshot must reflect what was granted and what wasn't."""
        pkg = create_handoff_package(
            self.call_id, "agent_A", "agent_B",
            "requires legal-aid specialist",
            self.pipeline_state, self.decision_aid, self.consent,
        )
        payload = apply_handoff_package(pkg)

        self.assertTrue(payload["consent_summary"]["recording"])
        self.assertTrue(payload["consent_summary"]["ai_analysis"])
        self.assertFalse(payload["consent_summary"]["data_for_improvement"])

    def test_timeline_preserved(self):
        """Case timeline must survive the handoff intact."""
        pkg = create_handoff_package(
            self.call_id, "agent_A", "agent_B",
            "requires legal-aid specialist",
            self.pipeline_state, self.decision_aid, self.consent,
        )
        payload = apply_handoff_package(pkg)

        self.assertEqual(payload["timeline"], self.original_timeline)

    def test_call_id_not_changed(self):
        """The handoff must preserve the SAME call_id — not create a new one."""
        pkg = create_handoff_package(
            self.call_id, "agent_A", "agent_B",
            "requires legal-aid specialist",
            self.pipeline_state, self.decision_aid, self.consent,
        )
        payload = apply_handoff_package(pkg)

        self.assertEqual(payload["call_id"], self.call_id)

    def test_original_state_not_mutated(self):
        """Creating a handoff must not mutate the original pipeline_state."""
        original_snapshot = json.dumps(self.pipeline_state, sort_keys=True)

        create_handoff_package(
            self.call_id, "agent_A", "agent_B",
            "requires legal-aid specialist",
            self.pipeline_state, self.decision_aid, self.consent,
        )

        after_snapshot = json.dumps(self.pipeline_state, sort_keys=True)
        self.assertEqual(original_snapshot, after_snapshot,
                         "Original pipeline_state must not be mutated")

    def test_full_payload_json_serializable(self):
        """The entire payload must be JSON-serializable without errors."""
        pkg = create_handoff_package(
            self.call_id, "agent_A", "agent_B",
            "requires legal-aid specialist",
            self.pipeline_state, self.decision_aid, self.consent,
        )
        payload = apply_handoff_package(pkg)

        try:
            serialized = json.dumps(payload)
        except (TypeError, ValueError) as e:
            self.fail(f"Payload is not JSON-serializable: {e}")

        # Round-trip: deserialize and compare
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized["risk_vector"], payload["risk_vector"])
        self.assertEqual(deserialized["svi"], payload["svi"])
        self.assertEqual(deserialized["evidence"], payload["evidence"])


if __name__ == "__main__":
    unittest.main()
