import sys
import os
import wave
import numpy as np

# Add Person 1 to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "Person 1"))
sys.path.append(os.path.join(BASE_DIR, "Person 4"))

from nhaa_core_pipeline import process_audio_chunk

file_path = "real_low_risk.wav"
with wave.open(file_path, 'rb') as wf:
    data = wf.readframes(wf.getnframes())
    audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

print("Running AI on audio chunk...")
result = process_audio_chunk(audio_array, "test_call_real")
print("AI Result:")
import json
print(json.dumps(result, indent=2))
