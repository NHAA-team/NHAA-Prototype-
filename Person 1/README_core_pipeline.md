# NHAA Core Pipeline (Person 1)

This module encapsulates the Core AI Pipeline designed for the NHAA Trauma Triage System. It takes an audio chunk and outputs an exact JSON message containing the transcription, silence events, stress vulnerability index (SVI), and associated risk dimensions.

## Requirements
- Python 3
- `numpy`
- `openai-whisper`
- `transformers`
- `torch`

## How to Call

You can import this directly into the main NHAA application.

```python
import numpy as np
from nhaa_core_pipeline import process_audio_chunk, reset_session

# Load your 16kHz float32 audio chunk (2-second window)
sample_rate = 16000
chunk_audio = np.random.normal(0, 0.05, sample_rate * 2).astype(np.float32)

# Pass the audio, a unique call_id string, and language code ("en", "hi", "hinglish")
# The pipeline automatically stores session context per call_id internally.
result_json = process_audio_chunk(
    audio_array=chunk_audio,
    call_id="call_12345",
    language="en"
)

print(result_json)

# If the call ends, clear the session:
reset_session("call_12345")
```

## Expected Return Output
The function returns a `dict` exactly matching the contract. It tracks the cumulative transcript, aggregates the sliding window logic, computes the 0-100 SVI based on the 8 keyword risk dimensions, and provides latencies.

## Latency Measurements
Tested on Apple Silicon / CPU-only inference environment without heavy optimization:
- **ASR**: ~0.02ms (Mock) / ~4.15s (Actual Whisper Small)
- **Silence Detection**: ~0.45ms
- **Risk Scorer**: ~0.02ms
- **SVI Aggregator**: ~0.01ms
