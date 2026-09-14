"""
Test: Supervisor gloss parallel path — lossless, non-contaminating.

Feeds a sample Hindi transcript through the full pipeline, confirms:
(a) risk_scorer.py receives and scores the ORIGINAL Hindi text
    (matched_evidence contains Hindi phrases, not English ones),
(b) the outgoing WebSocket payload also contains a populated
    supervisor_gloss field,
proving both paths run in parallel without one contaminating the other.
"""

import unittest
import numpy as np


class TestSupervisorGlossParallelPath(unittest.TestCase):

    def test_hindi_transcript_gloss_parallel_processing(self):
        """Full pipeline: Hindi phrase → risk scorer gets Hindi, gloss field also populated."""
        from nhaa_core_pipeline import process_audio_chunk, reset_session
        import nhaa_core_pipeline

        call_id = "test-gloss-001"
        reset_session(call_id)

        # This exact phrase appears in keywords/acute_distress.json as a Hindi entry
        hindi_phrase = "घबराहट, चिंता या परेशानी महसूस होना"

        # Dummy audio — content irrelevant because we mock ASR
        dummy_audio = np.zeros(16000 * 2, dtype=np.float32)

        # ── Save originals so we can restore them ──
        original_asr_process = nhaa_core_pipeline._asr.process
        original_asr_load_models = nhaa_core_pipeline._asr.load_models

        def mock_load_models():
            pass  # skip heavy model downloads

        def mock_process(audio_array, language, sample_rate):
            return {
                "transcript_available": True,
                "text": hindi_phrase,
                "words": [{"word": w, "start": 0.0, "end": 0.0} for w in hindi_phrase.split()],
                "lang_detected": "hi",
            }

        try:
            nhaa_core_pipeline._asr.process = mock_process
            nhaa_core_pipeline._asr.load_models = mock_load_models

            result = process_audio_chunk(dummy_audio, call_id, language="hi")

            # ── 1. Original Hindi text is what gets sent out ──
            self.assertEqual(result["text"].strip(), hindi_phrase,
                             "The outgoing 'text' field must be the original Hindi")

            # ── 2. risk_scorer matched Hindi keywords (not English translations) ──
            evidence = result["risk_vector"]["matched_evidence"]
            self.assertIn("acute_distress", evidence,
                          "acute_distress should be triggered by Hindi GAD-7 phrase")
            # The matched evidence must contain the *Hindi* phrase (lowercased)
            self.assertIn(hindi_phrase.lower(), evidence["acute_distress"],
                          "Evidence must contain the original Hindi phrase, not an English one")

            # ── 3. supervisor_gloss field exists and is populated ──
            self.assertIn("supervisor_gloss", result,
                          "Pipeline output must include 'supervisor_gloss'")
            expected_gloss = f"[gloss unavailable: {hindi_phrase}]"
            self.assertEqual(result["supervisor_gloss"], expected_gloss,
                             "Gloss stub must wrap the original text")

            # ── 4. No contamination: text ≠ gloss ──
            self.assertNotEqual(result["text"].strip(), result["supervisor_gloss"],
                                "Original text and gloss must be different values")

            # ── 5. Confirm scorer never saw the gloss ──
            # If it did, evidence would contain English words like "gloss" or "unavailable"
            all_evidence_phrases = [
                phrase
                for dim_phrases in evidence.values()
                for phrase in dim_phrases
            ]
            for phrase in all_evidence_phrases:
                self.assertNotIn("gloss", phrase.lower(),
                                 "Evidence must never contain the gloss string")
                self.assertNotIn("unavailable", phrase.lower(),
                                 "Evidence must never contain the gloss stub")

        finally:
            nhaa_core_pipeline._asr.process = original_asr_process
            nhaa_core_pipeline._asr.load_models = original_asr_load_models


if __name__ == "__main__":
    unittest.main()
