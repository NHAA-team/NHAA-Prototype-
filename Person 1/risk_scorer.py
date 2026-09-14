import os
import json

class RiskScorer:
    def __init__(self, keywords_dir=None):
        if keywords_dir is None:
            keywords_dir = os.path.join(os.path.dirname(__file__), "keywords")
        self.dimensions = [
            "acute_distress", "depression", "self_harm_risk", 
            "fear_of_retaliation", "intimidation", "dissociation", 
            "social_isolation", "chronic_trauma_indicators"
        ]
        self.keywords = {}
        
        for dim in self.dimensions:
            filepath = os.path.join(keywords_dir, f"{dim}.json")
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Missing keyword file: {filepath}")
                
            with open(filepath, "r", encoding="utf-8") as f:
                self.keywords[dim] = json.load(f)
                
    def process(self, transcript_text, silence_events):
        text_lower = transcript_text.lower()
        
        scores = {}
        matched_evidence = {}
        confidences = {}
        
        for dim in self.dimensions:
            matches = []
            for item in self.keywords[dim]:
                phrase = item["phrase"].lower()
                if phrase in text_lower:
                    if phrase not in matches:
                        matches.append(phrase)
            
            num_matches = len(matches)
            score = min(1.0, 0.5 * num_matches)
            
            if num_matches >= 2:
                conf = 0.9
            elif num_matches == 1:
                conf = 0.6
            else:
                conf = 0.0
                
            scores[dim] = score
            if matches:
                matched_evidence[dim] = matches
            confidences[dim] = conf
            
        has_mid_sentence_silence = False
        for event in silence_events:
            if event.get("placement") == "mid_sentence" and event.get("duration_sec", 0) > 2.0:
                has_mid_sentence_silence = True
                break
                
        if has_mid_sentence_silence:
            scores["dissociation"] = min(1.0, scores["dissociation"] + 0.5)
            if "dissociation" not in matched_evidence:
                matched_evidence["dissociation"] = []
            matched_evidence["dissociation"].append("mid_sentence silence > 2s")
            
            if confidences["dissociation"] == 0.0:
                confidences["dissociation"] = 0.3
            else:
                confidences["dissociation"] = min(1.0, confidences["dissociation"] + 0.3)
                
        overall_confidence = sum(confidences.values()) / len(confidences) if confidences else 0.0
        
        return {
            "scores": scores,
            "confidence": confidences,
            "matched_evidence": matched_evidence,
            "overall_confidence": overall_confidence
        }

if __name__ == "__main__":
    scorer = RiskScorer()
    
    sample_text = "I feel like killing myself. They will come back. They threatened to kill my son."
    sample_silence = [{"start_sec": 1.0, "duration_sec": 2.5, "placement": "mid_sentence"}]
    
    result = scorer.process(sample_text, sample_silence)
    
    import pprint
    pprint.pprint(result)
    
    assert result["scores"]["self_harm_risk"] >= 0.5
    assert result["scores"]["fear_of_retaliation"] >= 0.5
    assert result["scores"]["intimidation"] >= 0.5
    assert result["scores"]["dissociation"] >= 0.5
    
    print("Test passed: Risk scores and evidence computed correctly.")
