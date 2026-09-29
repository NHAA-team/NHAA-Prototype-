import time
from asr import ASRModule
from silence_detector import SilenceDetector
from risk_scorer import RiskScorer
from svi_aggregator import SVIAggregator
from supervisor_gloss import generate_gloss

# Pre-instantiate models as singletons for the package
_asr = ASRModule()
_silence_det = SilenceDetector(sample_rate=16000)
_scorer = RiskScorer()
_aggregator = SVIAggregator()

# Store session state by call_id
_call_sessions = {}

def process_audio_chunk(audio_array, call_id, language="en"):
    """
    Entry-point function for processing a single audio chunk.
    Maintains transcript and silence history across chunks for a given call_id.
    """
    _asr.load_models()
    
    if call_id not in _call_sessions:
        _call_sessions[call_id] = {
            "transcript_text": "",
            "words_list": [],
            "silences": [],
            "chunk_index": 0
        }
        
    session = _call_sessions[call_id]
    chunk_index = session["chunk_index"]
    window_size_sec = 2.0
    
    # 1. ASR
    t0 = time.perf_counter()
    asr_result = _asr.process(audio_array, language, 16000)
    t1 = time.perf_counter()
    lat_asr = (t1 - t0) * 1000.0
    
    chunk_words = []
    if asr_result.get("transcript_available"):
        chunk_text = asr_result.get("text", "")
        chunk_words = asr_result.get("words", [])
        
        session["transcript_text"] += " " + chunk_text
        for w in chunk_words:
            w["start"] += chunk_index * window_size_sec
            w["end"] += chunk_index * window_size_sec
        session["words_list"].extend(chunk_words)
        
    # 2. Silence Detector
    t2 = time.perf_counter()
    chunk_silences = _silence_det.process(audio_array, chunk_words)
    for s in chunk_silences:
        s["start_sec"] += chunk_index * window_size_sec
    session["silences"].extend(chunk_silences)
    t3 = time.perf_counter()
    lat_sil = (t3 - t2) * 1000.0
    
    # 3. Risk Scorer
    t4 = time.perf_counter()
    risk_result = _scorer.process(session["transcript_text"], session["silences"])
    
    # This gloss output must never be passed to risk_scorer.py or any scoring function. It exists for supervisor readability only.
    gloss = generate_gloss(session["transcript_text"], asr_result.get("lang_detected", language))
    
    t5 = time.perf_counter()
    lat_risk = (t5 - t4) * 1000.0
    
    # 4. SVI Aggregator
    t6 = time.perf_counter()
    svi_result = _aggregator.process(risk_result["scores"])
    t7 = time.perf_counter()
    lat_svi = (t7 - t6) * 1000.0
    
    session["chunk_index"] += 1
    
    return {
        "type": "transcript_update",
        "text": session["transcript_text"].strip(),
        "supervisor_gloss": gloss,
        "words": session["words_list"],
        "lang_detected": asr_result.get("lang_detected", language),
        "risk_vector": {
            "scores": risk_result["scores"],
            "confidence": risk_result["confidence"],
            "matched_evidence": risk_result["matched_evidence"],
            "overall_confidence": risk_result["overall_confidence"]
        },
        "svi": svi_result,
        "silence_events": chunk_silences,
        "latencies_ms": {
            "asr": round(lat_asr, 2),
            "silence": round(lat_sil, 2),
            "risk_scorer": round(lat_risk, 2),
            "svi": round(lat_svi, 2)
        }
    }

def reset_session(call_id):
    if call_id in _call_sessions:
        del _call_sessions[call_id]
