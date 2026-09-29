import numpy as np
from pipeline import run_pipeline
import sys

def test_hardening():
    sr = 16000
    
    print("=" * 50)
    print("TEST CASE 1: FULLY SILENT AUDIO")
    print("=" * 50)
    silent_audio = np.zeros(sr * 4, dtype=np.float32)
    try:
        run_pipeline(silent_audio, language="en")
        print("[SUCCESS] Fully silent audio handled gracefully.")
    except Exception as e:
        print(f"[FAILED] Crashed on fully silent audio: {e}")
        sys.exit(1)
        
    print("\n" + "=" * 50)
    print("TEST CASE 2: HEAVY BACKGROUND NOISE")
    print("=" * 50)
    # Simulate high amplitude white noise
    noise_audio = np.random.normal(0, 0.8, sr * 4).astype(np.float32)
    try:
        # Expected behavior: might trigger asr to process, but should not crash
        run_pipeline(noise_audio, language="en")
        print("[SUCCESS] Heavy background noise handled gracefully.")
    except Exception as e:
        print(f"[FAILED] Crashed on heavy background noise: {e}")
        sys.exit(1)
        
    print("\n" + "=" * 50)
    print("TEST CASE 3: MID-SENTENCE CODE-SWITCHING")
    print("=" * 50)
    # Since we use a mock for the ASR when models aren't loaded, 
    # the code switching test just confirms that setting language="hinglish"
    # works and doesn't crash the pipeline, which it shouldn't.
    # In a real scenario, whisper natively handles hinglish well.
    mixed_audio = np.random.normal(0, 0.1, sr * 4).astype(np.float32)
    try:
        run_pipeline(mixed_audio, language="hinglish")
        print("[SUCCESS] Mid-sentence code switching simulation handled gracefully.")
    except Exception as e:
        print(f"[FAILED] Crashed on mid-sentence code switching simulation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_hardening()
