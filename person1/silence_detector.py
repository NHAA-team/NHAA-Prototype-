import numpy as np

class SilenceDetector:
    # Global threshold used for mid_sentence classification when no personal
    # baseline is available (either before calibration or when calibration
    # collected too few data points).
    GLOBAL_MID_SENTENCE_THRESHOLD_SEC = 1.2

    def __init__(self, threshold=0.010, min_duration=0.5, frame_size_ms=20,
                 sample_rate=16000, calibration_window_sec=12.0):
        self.threshold = threshold
        self.min_duration = min_duration
        self.frame_size_ms = frame_size_ms
        self.sample_rate = sample_rate
        self.frame_length = int(sample_rate * (frame_size_ms / 1000.0))
        self.calibration_window_sec = calibration_window_sec

        # --- Calibration state ---
        self._calibration_gaps = []          # inter-word gap durations during calibration
        self._audio_processed_sec = 0.0      # cumulative audio duration processed
        self._personal_mean_gap = None       # mean of calibration gaps (set after calibration)
        self._personal_std_gap = None        # std of calibration gaps  (set after calibration)
        self._calibrated = False             # True once calibration window has elapsed
        self._using_personal_baseline = False  # True if personal baseline computed successfully

    def process(self, audio_array, asr_words):
        if len(audio_array) == 0:
            return []
            
        if audio_array.dtype != np.float32:
            audio_array = audio_array.astype(np.float32)

        chunk_duration_sec = len(audio_array) / self.sample_rate

        num_frames = len(audio_array) // self.frame_length
        silence_events = []
        
        current_silence_start = None
        
        for i in range(num_frames):
            frame = audio_array[i * self.frame_length : (i + 1) * self.frame_length]
            rms = np.sqrt(np.mean(frame**2))
            
            time_sec = i * (self.frame_size_ms / 1000.0)
            
            if rms < self.threshold:
                if current_silence_start is None:
                    current_silence_start = time_sec
            else:
                if current_silence_start is not None:
                    duration = time_sec - current_silence_start
                    if duration >= self.min_duration:
                        silence_events.append({
                            "start_sec": current_silence_start,
                            "duration_sec": duration
                        })
                    current_silence_start = None
                    
        if current_silence_start is not None:
            time_sec = num_frames * (self.frame_size_ms / 1000.0)
            duration = time_sec - current_silence_start
            if duration >= self.min_duration:
                silence_events.append({
                    "start_sec": current_silence_start,
                    "duration_sec": duration
                })
                
        for event in silence_events:
            event["placement"] = self._classify_placement(event, asr_words)

        # Accumulate processed audio duration and finalize calibration
        # if the window has just been crossed.
        self._audio_processed_sec += chunk_duration_sec
        if not self._calibrated and self._audio_processed_sec >= self.calibration_window_sec:
            self._finalize_calibration()

        return silence_events

    # ------------------------------------------------------------------
    # Calibration helpers
    # ------------------------------------------------------------------

    def _finalize_calibration(self):
        """Compute personal baseline from collected gaps, or fall back."""
        if len(self._calibration_gaps) >= 3:
            self._personal_mean_gap = float(np.mean(self._calibration_gaps))
            self._personal_std_gap = float(np.std(self._calibration_gaps))
            self._using_personal_baseline = True
        else:
            # Insufficient data — keep using global threshold
            self._using_personal_baseline = False
        self._calibrated = True

    def _get_mid_sentence_threshold(self):
        """Return the effective mid-sentence duration threshold."""
        if self._using_personal_baseline and self._personal_mean_gap is not None:
            computed = self._personal_mean_gap + 2 * self._personal_std_gap
            return max(1.0, computed)  # floor of 1.0s
        return self.GLOBAL_MID_SENTENCE_THRESHOLD_SEC

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def _classify_placement(self, event, asr_words):
        if not asr_words:
            return "inter_turn"
            
        event_start = event["start_sec"]
        event_end = event_start + event["duration_sec"]
        
        word_before = None
        word_after = None
        
        for i, word_info in enumerate(asr_words):
            if word_info["end"] <= event_start:
                word_before = word_info
                if i + 1 < len(asr_words):
                    word_after = asr_words[i+1]
        
        if word_before and word_after and word_after["start"] >= event_end:
            # During calibration: record the gap but never flag as mid_sentence
            if not self._calibrated:
                gap_duration = event["duration_sec"]
                self._calibration_gaps.append(gap_duration)
                return "inter_word"

            punctuation = [".", "?", "!", ","]
            has_punct = any(p in word_before["word"] for p in punctuation)
            
            if not has_punct and event["duration_sec"] > self._get_mid_sentence_threshold():
                return "mid_sentence"
            else:
                return "inter_word"
                
        return "inter_turn"

    # ------------------------------------------------------------------
    # Transparency / serialization
    # ------------------------------------------------------------------

    def to_dict(self):
        """Expose current calibration state for the agent console."""
        personal_threshold = None
        if self._personal_mean_gap is not None and self._personal_std_gap is not None:
            personal_threshold = round(
                max(1.0, self._personal_mean_gap + 2 * self._personal_std_gap), 4
            )

        return {
            "calibrated": self._calibrated,
            "using_personal_baseline": self._using_personal_baseline,
            "personal_mean_gap": (
                round(self._personal_mean_gap, 4)
                if self._personal_mean_gap is not None else None
            ),
            "personal_std_gap": (
                round(self._personal_std_gap, 4)
                if self._personal_std_gap is not None else None
            ),
            "personal_threshold": personal_threshold,
            "calibration_gaps_recorded": len(self._calibration_gaps),
            "audio_processed_sec": round(self._audio_processed_sec, 2),
            "calibration_window_sec": self.calibration_window_sec,
            "global_threshold_sec": self.GLOBAL_MID_SENTENCE_THRESHOLD_SEC,
        }

if __name__ == "__main__":
    detector = SilenceDetector(threshold=0.010, min_duration=0.5)
    sr = 16000
    
    # 1s noise (amp 0.08)
    noise1 = np.random.normal(0, 0.08, sr * 1).astype(np.float32)
    # 2s near-silence (amp 0.002)
    silence2 = np.random.normal(0, 0.002, sr * 2).astype(np.float32)
    # 1s noise (amp 0.08)
    noise3 = np.random.normal(0, 0.08, sr * 1).astype(np.float32)
    
    synthetic_array = np.concatenate([noise1, silence2, noise3])
    
    # Mock ASR words
    asr_words = [
        {"word": "hello", "start": 0.5, "end": 0.8},
        {"word": "world", "start": 3.2, "end": 3.6} 
    ]
    
    events = detector.process(synthetic_array, asr_words)
    print("Detected Silence Events:", events)
    assert len(events) == 1
    assert abs(events[0]["start_sec"] - 1.0) < 0.1
    assert abs(events[0]["duration_sec"] - 2.0) < 0.1
    # With only 4s of audio, calibration hasn't finished (default window=12s),
    # so the gap is recorded and classified as inter_word during calibration.
    assert events[0]["placement"] == "inter_word"
    print("Test passed: Detected and classified synthetic silence correctly.")
    print("Detector state:", detector.to_dict())
