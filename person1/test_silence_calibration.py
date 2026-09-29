"""
Tests for adaptive per-call threshold personalization in SilenceDetector.

(a) Slow deliberate speaker: confirms personal baseline is learned, and a 1.8s
    gap post-calibration is NOT flagged as mid_sentence (within their range),
    while the old fixed 1.2s threshold WOULD have flagged it.

(b) Insufficient calibration data: confirms fallback to the global 1.2s
    threshold when fewer than 3 gaps are recorded.
"""

import unittest
import numpy as np
from silence_detector import SilenceDetector


def _make_speech_segment(duration_sec, sr=16000, amplitude=0.08):
    """Generate a segment of noise that reads as 'speech' (above energy threshold)."""
    n_samples = int(sr * duration_sec)
    return np.random.normal(0, amplitude, n_samples).astype(np.float32)


def _make_silence_segment(duration_sec, sr=16000, amplitude=0.002):
    """Generate a segment of near-silence (below energy threshold)."""
    n_samples = int(sr * duration_sec)
    return np.random.normal(0, amplitude, n_samples).astype(np.float32)


class TestSlowSpeakerPersonalizedThreshold(unittest.TestCase):
    """
    (a) Simulate a calibration-phase caller who naturally pauses ~1.5s
    between most words (slow, deliberate speaker).
    """

    def test_slow_speaker_1_8s_not_flagged(self):
        """
        A caller who naturally pauses ~1.5s with natural variation (some gaps
        shorter, some longer) should have a personal threshold high enough
        that a 1.8s gap post-calibration is NOT flagged as mid_sentence.
        """
        sr = 16000
        detector = SilenceDetector(
            threshold=0.010,
            min_duration=0.5,
            sample_rate=sr,
            calibration_window_sec=12.0,
        )

        # Build calibration audio with varied gaps around 1.5s
        # Gaps: [1.2, 1.8, 1.3, 1.7, 1.5] → mean=1.5, std≈0.24
        # Threshold = max(1.0, 1.5 + 2*0.24) = max(1.0, 1.98) = 1.98
        segments = []
        asr_words = []
        t = 0.0
        gap_durations = [1.2, 1.8, 1.3, 1.7, 1.5]
        word_names = ["hello", "my", "name", "is", "John", "Smith"]

        # We add a small padding (0.05s) to word start times after each
        # silent gap so the ASR word clearly starts AFTER the silence event
        # ends, avoiding floating-point edge cases in the frame-based detector.
        WORD_PAD = 0.05

        for word_idx in range(len(word_names)):
            speech_dur = 0.8
            segments.append(_make_speech_segment(speech_dur, sr))
            asr_words.append({
                "word": word_names[word_idx],
                "start": t + (WORD_PAD if word_idx > 0 else 0.0),
                "end": t + speech_dur,
            })
            t += speech_dur

            if word_idx < len(gap_durations):
                gap = gap_durations[word_idx]
                segments.append(_make_silence_segment(gap, sr))
                t += gap

        calibration_audio = np.concatenate(segments)
        self.assertGreaterEqual(len(calibration_audio) / sr, 12.0)

        # Process calibration chunk
        detector.process(calibration_audio, asr_words)

        self.assertTrue(detector._calibrated)
        self.assertTrue(detector._using_personal_baseline)
        self.assertAlmostEqual(detector._personal_mean_gap, 1.5, delta=0.15)

        personal_threshold = detector._get_mid_sentence_threshold()
        # threshold should be > 1.8 for this speaker
        self.assertGreater(personal_threshold, 1.8,
                           f"Personal threshold {personal_threshold:.2f} should exceed 1.8")

        # --- Confirm 1.8s gap WOULD have been flagged under old global threshold ---
        self.assertGreater(1.8, SilenceDetector.GLOBAL_MID_SENTENCE_THRESHOLD_SEC,
                           "1.8s exceeds the old global 1.2s threshold")

        # --- Post-calibration: 1.8s gap should NOT be mid_sentence ---
        post_segments = []
        post_words = []
        t2 = 0.0

        post_segments.append(_make_speech_segment(0.5, sr))
        post_words.append({"word": "I", "start": t2, "end": t2 + 0.5})
        t2 += 0.5

        post_segments.append(_make_silence_segment(1.8, sr))
        t2 += 1.8

        post_segments.append(_make_speech_segment(0.8, sr))
        post_words.append({"word": "understand", "start": t2 + WORD_PAD, "end": t2 + 0.8})
        t2 += 0.8

        post_audio = np.concatenate(post_segments)
        events_post = detector.process(post_audio, post_words)

        long_gaps = [e for e in events_post if e["duration_sec"] > 1.5]
        self.assertEqual(len(long_gaps), 1, "Should detect exactly one ~1.8s gap")
        self.assertEqual(long_gaps[0]["placement"], "inter_word",
                         "1.8s gap should be inter_word for this slow speaker, "
                         "NOT mid_sentence")

        # Verify to_dict() exposes the baseline
        state = detector.to_dict()
        self.assertTrue(state["calibrated"])
        self.assertTrue(state["using_personal_baseline"])
        self.assertIsNotNone(state["personal_mean_gap"])
        self.assertIsNotNone(state["personal_std_gap"])
        self.assertIsNotNone(state["personal_threshold"])
        print(f"\n[to_dict] This caller's baseline pause is "
              f"{state['personal_mean_gap']:.2f}s, "
              f"deviations flagged above {state['personal_threshold']:.2f}s")



class TestFallbackToGlobalThreshold(unittest.TestCase):
    """
    (b) Confirms the fallback to global threshold works correctly when
    calibration data is insufficient (fewer than 3 inter-word gaps).
    """

    def test_insufficient_calibration_falls_back(self):
        sr = 16000
        detector = SilenceDetector(
            threshold=0.010,
            min_duration=0.5,
            sample_rate=sr,
            calibration_window_sec=12.0,
        )

        # Build ~13s of mostly continuous speech with only 1 gap
        # 6s speech, 1.5s silence, 6s speech = 13.5s total, only 1 gap
        segments = [
            _make_speech_segment(6.0, sr),
            _make_silence_segment(1.5, sr),
            _make_speech_segment(6.0, sr),
        ]
        audio = np.concatenate(segments)
        self.assertGreaterEqual(len(audio) / sr, 12.0)

        asr_words = [
            {"word": "once", "start": 0.0, "end": 0.5},
            {"word": "upon", "start": 0.6, "end": 1.0},
            # These two words bracket the silence gap at 6.0–7.5s
            {"word": "time", "start": 5.5, "end": 6.0},
            {"word": "there", "start": 7.5, "end": 8.0},
            {"word": "was", "start": 8.1, "end": 8.5},
            {"word": "a", "start": 8.6, "end": 8.8},
            {"word": "kingdom", "start": 9.0, "end": 9.8},
        ]

        events = detector.process(audio, asr_words)

        # Calibration should have completed but fallen back to global
        self.assertTrue(detector._calibrated)
        self.assertFalse(detector._using_personal_baseline,
                         "Should fall back: only 1 gap < minimum 3")
        self.assertIsNone(detector._personal_mean_gap)
        self.assertIsNone(detector._personal_std_gap)

        # The effective threshold should be the global one
        self.assertEqual(detector._get_mid_sentence_threshold(),
                         SilenceDetector.GLOBAL_MID_SENTENCE_THRESHOLD_SEC)

        # --- Post-calibration: a 1.5s gap SHOULD be flagged as mid_sentence ---
        post_segments = []
        post_words = []
        t2 = 0.0

        post_segments.append(_make_speech_segment(0.5, sr))
        post_words.append({"word": "I", "start": t2, "end": t2 + 0.5})
        t2 += 0.5

        post_segments.append(_make_silence_segment(1.5, sr))
        t2 += 1.5

        post_segments.append(_make_speech_segment(0.8, sr))
        post_words.append({"word": "see", "start": t2, "end": t2 + 0.8})
        t2 += 0.8

        post_audio = np.concatenate(post_segments)
        events_post = detector.process(post_audio, post_words)

        long_gaps = [e for e in events_post if e["duration_sec"] > 1.2]
        self.assertEqual(len(long_gaps), 1, "Should detect the ~1.5s gap")
        self.assertEqual(long_gaps[0]["placement"], "mid_sentence",
                         "1.5s > 1.2s global threshold → mid_sentence")

        # Verify to_dict() shows fallback state
        state = detector.to_dict()
        self.assertTrue(state["calibrated"])
        self.assertFalse(state["using_personal_baseline"])
        self.assertIsNone(state["personal_threshold"])
        print(f"\n[to_dict] Fallback active — using global threshold "
              f"{state['global_threshold_sec']}s")


if __name__ == "__main__":
    unittest.main()
