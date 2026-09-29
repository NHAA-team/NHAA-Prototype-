import time
import json
import numpy as np

from asr import ASRModule
from silence_detector import SilenceDetector
from risk_scorer import RiskScorer
from svi_aggregator import SVIAggregator
from supervisor_gloss import generate_gloss

def run_pipeline(audio_array, sample_rate=16000, language="en"):
    # Initialize modules
    asr = ASRModule()
    silence_det = SilenceDetector(sample_rate=sample_rate)
    scorer = RiskScorer()
    aggregator = SVIAggregator()
    
    # Load models if needed
    asr.load_models()
    
    # We will process in 2-second windows
    window_size_sec = 2.0
    window_samples = int(sample_rate * window_size_sec)
    num_chunks = len(audio_array) // window_samples
    
    if len(audio_array) % window_samples != 0:
        num_chunks += 1
        
    full_transcript_text = ""
    full_words_list = []
    
    for i in range(num_chunks):
        start_idx = i * window_samples
        end_idx = min((i + 1) * window_samples, len(audio_array))
        chunk = audio_array[start_idx:end_idx]
        
        # 1. ASR
        t0 = time.perf_counter()
        asr_result = asr.process(chunk, language, sample_rate)
        t1 = time.perf_counter()
        lat_asr = (t1 - t0) * 1000.0
        
        chunk_text = ""
        chunk_words = []
        if asr_result.get("transcript_available"):
            chunk_text = asr_result.get("text", "")
            chunk_words = asr_result.get("words", [])
            full_transcript_text += " " + chunk_text
            # adjust timestamps
            for w in chunk_words:
                w["start"] += i * window_size_sec
                w["end"] += i * window_size_sec
            full_words_list.extend(chunk_words)
            
        # 2. Silence Detector
        t2 = time.perf_counter()
        # For true sliding window, we might want to pass the full audio so far
        # But for this chunk-based contract, we just process the chunk
        silences = silence_det.process(chunk, chunk_words)
        # adjust silence timestamps
        for s in silences:
            s["start_sec"] += i * window_size_sec
        t3 = time.perf_counter()
        lat_sil = (t3 - t2) * 1000.0
        
        # 3. Risk Scorer
        t4 = time.perf_counter()
        # the scorer should see the accumulated transcript to detect full phrases
        risk_result = scorer.process(full_transcript_text, silences)
        
        # This gloss output must never be passed to risk_scorer.py or any scoring function. It exists for supervisor readability only.
        gloss = generate_gloss(full_transcript_text, asr_result.get("lang_detected", language))
        
        t5 = time.perf_counter()
        lat_risk = (t5 - t4) * 1000.0
        
        # 4. SVI Aggregator
        t6 = time.perf_counter()
        svi_result = aggregator.process(risk_result["scores"])
        t7 = time.perf_counter()
        lat_svi = (t7 - t6) * 1000.0
        
        # Build Output JSON matching contract
        output = {
            "type": "transcript_update",
            "text": full_transcript_text.strip(),
            "supervisor_gloss": gloss,
            "words": full_words_list,
            "lang_detected": asr_result.get("lang_detected", language),
            "risk_vector": {
                "scores": risk_result["scores"],
                "confidence": risk_result["confidence"],
                "matched_evidence": risk_result["matched_evidence"],
                "overall_confidence": risk_result["overall_confidence"]
            },
            "svi": svi_result,
            "silence_events": silences,
            "latencies_ms": {
                "asr": round(lat_asr, 2),
                "silence": round(lat_sil, 2),
                "risk_scorer": round(lat_risk, 2),
                "svi": round(lat_svi, 2)
            }
        }
        
        print(f"--- Chunk {i+1} ---")
        print(json.dumps(output, indent=2, ensure_ascii=False))
        print()

if __name__ == "__main__":
    import wave
    
    sr = 16000
    
    # Let's create a synthetic array directly
    # 2s noise, 2s silence, 2s noise
    print("Generating synthetic 6-second audio test...")
    noise1 = np.random.normal(0, 0.05, sr * 2).astype(np.float32)
    silence = np.zeros(sr * 2, dtype=np.float32)
    noise2 = np.random.normal(0, 0.05, sr * 2).astype(np.float32)
    
    test_audio = np.concatenate([noise1, silence, noise2])
    
    run_pipeline(test_audio, language="en")
