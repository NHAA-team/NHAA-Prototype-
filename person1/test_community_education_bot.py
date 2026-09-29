"""
Tests for CommunityEducationBot.

(a) Normal FAQ question → correct intent and response.
(b) First-person distress phrase → crisis_language_detector fires,
    14566 hand-off message returned instead of FAQ.
(c) Crisis flag is sticky — subsequent messages still get hand-off.
(d) Hindi FAQ question → correct Hindi response.
(e) Unrecognized input → graceful fallback with 14566 pointer.
"""

import unittest
from community_education_bot import (
    CommunityEducationBot,
    crisis_language_detector,
    detect_language,
)


class TestNormalFAQResponse(unittest.TestCase):
    """(a) Normal questions return correct FAQ responses."""

    def setUp(self):
        self.bot = CommunityEducationBot()

    def test_how_to_file_complaint_english(self):
        result = self.bot.respond("how do I file a complaint")
        self.assertEqual(result["matched_intent"], "how_to_report")
        self.assertEqual(result["language"], "en")
        self.assertIn("14566", result["response"])
        self.assertIn("FIR", result["response"])

    def test_hindi_complaint_question(self):
        result = self.bot.respond("complaint kaise karu")
        self.assertEqual(result["matched_intent"], "how_to_report")
        # "kaise karu" is romanised Hindi → detected as English by heuristic
        # but the intent should still match correctly
        self.assertIn("complaint", result["response"].lower())

    def test_devanagari_question(self):
        result = self.bot.respond("शिकायत कैसे करें")
        self.assertEqual(result["language"], "hi")
        # Should match how_to_report via "shikayat kaise karein" trigger
        # (Devanagari version)
        self.assertEqual(result["matched_intent"], "how_to_report")

    def test_what_is_14566(self):
        result = self.bot.respond("what is 14566")
        self.assertEqual(result["matched_intent"], "what_is_14566")
        self.assertIn("NHAA", result["response"])

    def test_legal_aid(self):
        result = self.bot.respond("what legal aid is available")
        self.assertEqual(result["matched_intent"], "legal_aid_available")
        self.assertIn("NALSA", result["response"])

    def test_confidentiality(self):
        result = self.bot.respond("is it confidential")
        self.assertEqual(result["matched_intent"], "confidentiality")
        self.assertIn("confidential", result["response"].lower())

    def test_shelter(self):
        result = self.bot.respond("I need a shelter home")
        self.assertEqual(result["matched_intent"], "shelter_and_protection")

    def test_sc_st_act(self):
        result = self.bot.respond("what is SC ST act")
        self.assertEqual(result["matched_intent"], "what_is_sc_st_act")


class TestCrisisDetectorAndRedirect(unittest.TestCase):
    """(b) Distress phrases trigger crisis redirect, not FAQ."""

    def setUp(self):
        self.bot = CommunityEducationBot()

    def test_crisis_detector_self_harm_english(self):
        """A self_harm_risk.json phrase must trigger the detector."""
        self.assertTrue(
            crisis_language_detector("I want to end my life"),
            "Self-harm phrase must trigger crisis detector",
        )

    def test_crisis_detector_self_harm_hinglish(self):
        self.assertTrue(
            crisis_language_detector(
                "main apni zindagi khatam karna chahta hu"
            ),
        )

    def test_crisis_detector_acute_distress_hindi(self):
        """An acute_distress.json phrase must also trigger."""
        self.assertTrue(
            crisis_language_detector("घबराहट, चिंता या परेशानी महसूस होना"),
        )

    def test_crisis_detector_normal_text(self):
        """A normal FAQ question must NOT trigger the detector."""
        self.assertFalse(
            crisis_language_detector("how do I file a complaint"),
        )

    def test_respond_returns_handoff_on_crisis(self):
        """
        When a user sends a self-harm phrase, the bot must return
        the 14566 hand-off message, NOT a normal FAQ response.
        """
        result = self.bot.respond("I feel like killing myself")

        self.assertEqual(result["matched_intent"], "crisis_redirect")
        self.assertIn("14566", result["response"])
        self.assertIn("not alone", result["response"].lower())
        # Must NOT be a normal FAQ intent
        self.assertNotEqual(result["matched_intent"], "how_to_report")
        self.assertNotEqual(result["matched_intent"], "fallback")

    def test_respond_returns_handoff_hinglish_crisis(self):
        result = self.bot.respond(
            "mujhe ab aur nahi jeena, sab kuch khatam karna hai"
        )
        self.assertEqual(result["matched_intent"], "crisis_redirect")
        self.assertIn("14566", result["response"])

    def test_crisis_flag_is_sticky(self):
        """
        Once crisis is triggered, ALL subsequent messages should get
        the hand-off response, even normal FAQ questions.
        """
        # First: trigger crisis
        r1 = self.bot.respond("I want to end my life")
        self.assertEqual(r1["matched_intent"], "crisis_redirect")

        # Second: ask a normal FAQ question
        r2 = self.bot.respond("how do I file a complaint")
        self.assertEqual(
            r2["matched_intent"],
            "crisis_redirect",
            "After crisis trigger, even normal questions must get hand-off",
        )
        self.assertIn("14566", r2["response"])

    def test_crisis_handoff_in_detected_language(self):
        """Hand-off message should be in the detected language."""
        result = self.bot.respond(
            "मुझे मर जाना चाहिए, main apni zindagi khatam karna chahta hu"
        )
        # Mixed Devanagari + Latin → hinglish
        self.assertEqual(result["language"], "hinglish")
        self.assertEqual(result["matched_intent"], "crisis_redirect")


class TestFallbackResponse(unittest.TestCase):
    """(e) Unrecognized input returns graceful fallback."""

    def setUp(self):
        self.bot = CommunityEducationBot()

    def test_fallback_on_gibberish(self):
        result = self.bot.respond("xyzzy foobar baz quux")
        self.assertEqual(result["matched_intent"], "fallback")
        self.assertIn("14566", result["response"])

    def test_fallback_on_empty(self):
        result = self.bot.respond("")
        self.assertEqual(result["matched_intent"], "fallback")


class TestLanguageDetection(unittest.TestCase):
    """Verify the lightweight language heuristic."""

    def test_english(self):
        self.assertEqual(detect_language("how do I report"), "en")

    def test_hindi(self):
        self.assertEqual(detect_language("शिकायत कैसे करें"), "hi")

    def test_hinglish(self):
        self.assertEqual(
            detect_language("mujhe बहुत dar lag raha hai"), "hinglish"
        )


if __name__ == "__main__":
    unittest.main()
