import numpy as np
import warnings

warnings.filterwarnings("ignore")

class ASRModule:
    def __init__(self):
        self.whisper_model = None
        self.hindi_pipeline = None
        self._models_loaded = False

    def load_models(self):
        if self._models_loaded:
            return
        print("Loading models... This may take a while.")
        try:
            import whisper
            self.whisper_model = whisper.load_model("small")
        except ImportError:
            print("whisper not installed. Use: pip install openai-whisper")
        
        try:
            from transformers import pipeline
            self.hindi_pipeline = pipeline("automatic-speech-recognition", model="ai4bharat/wav2vec2-large-xlsr-53-hindi")
        except ImportError:
            print("transformers not installed. Use: pip install transformers torch")
        self._models_loaded = True

    def process(self, audio_array, language, sample_rate=16000):
        if audio_array.dtype != np.float32:
            audio_array = audio_array.astype(np.float32)

        rms = np.sqrt(np.mean(audio_array**2))
        if rms < 0.010: 
            return {"transcript_available": False}

        if not self._models_loaded:
            self.load_models()

        if language in ["en", "hinglish"]:
            if self.whisper_model is None:
                return {"transcript_available": False}
            
            result = self.whisper_model.transcribe(audio_array, word_timestamps=True)
            text = result.get("text", "").strip()
            
            words = []
            for segment in result.get("segments", []):
                for word in segment.get("words", []):
                    words.append({
                        "word": word["word"].strip(),
                        "start": word["start"],
                        "end": word["end"]
                    })
                    
            if not text:
                return {"transcript_available": False}
                
            return {
                "transcript_available": True,
                "text": text,
                "words": words,
                "lang_detected": result.get("language", language)
            }
            
        elif language == "hi":
            if self.hindi_pipeline is None:
                return {"transcript_available": False}
            
            result = self.hindi_pipeline(audio_array)
            text = result.get("text", "")
            
            if not text:
                return {"transcript_available": False}
            
            words = [{"word": w, "start": 0.0, "end": 0.0} for w in text.split()]
            
            return {
                "transcript_available": True,
                "text": text,
                "words": words,
                "lang_detected": "hi"
            }
            
        return {"transcript_available": False}

if __name__ == "__main__":
    asr = ASRModule()
    
    print("Testing ASR Module with 5 seconds of silence...")
    silent_audio = np.zeros(16000 * 5, dtype=np.float32)
    
    try:
        result = asr.process(silent_audio, "en")
        print("Result:", result)
        assert result.get("transcript_available") is False
        print("Test passed: Handled silence correctly.")
    except Exception as e:
        print("Test failed: Crashed on silent audio.")
        print(e)
