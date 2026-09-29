import os
import json

from semantic_matcher import SemanticMatcher
from corroboration_gate import apply_corroboration

class RiskScorer:
    def __init__(self, keywords_dir=None, enable_semantic=True):
        self.keywords_dir = keywords_dir
        self.enable_semantic = enable_semantic
        
        self.exact_keywords = {}
        if keywords_dir:
            for fname in os.listdir(keywords_dir):
                if fname.endswith('.json'):
                    dim = fname.replace('.json', '')
                    with open(os.path.join(keywords_dir, fname), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.exact_keywords[dim] = [
                            {"phrase": item["phrase"].lower(), "weight": item.get("weight", 1.0)} 
                            for item in data
                        ]
                        
        if self.enable_semantic:
            self.semantic_matcher = SemanticMatcher(keywords_dir)
            
    def _check_exact(self, text):
        res = {}
        text_lower = text.lower()
        for dim, kw_list in self.exact_keywords.items():
            for kw in kw_list:
                if kw['weight'] < 0:
                    continue # Hard negative, ignore for exact matching
                if kw['phrase'] in text_lower:
                    if dim not in res:
                        res[dim] = []
                    res[dim].append(kw['phrase'])
        return res
        
    def process(self, transcript_text, speaker_diarization=None):
        exact_res = self._check_exact(transcript_text)
        sem_res = {}
        if self.enable_semantic:
            sem_res = self.semantic_matcher.match(transcript_text)
            
        scores = {}
        signal_sources = {}
        
        dims = set(exact_res.keys()).union(set(sem_res.keys()))
        for dim in dims:
            exact_hits = exact_res.get(dim, [])
            sem_hits = sem_res.get(dim, [])
            
            score = 0.0
            sources = {"lexical": 0, "semantic": 0, "silence": 0}
            
            if exact_hits:
                score = 1.0 # Exact match is 1.0
                sources["lexical"] = 1.0
            elif sem_hits:
                best_sim = max([h['similarity'] for h in sem_hits])
                if best_sim >= self.semantic_matcher.threshold:
                    score = 0.70 # Full semantic hit
                else:
                    score = 0.45 # Partial semantic hit
                sources["semantic"] = score
                    
            if score > 0:
                scores[dim] = score
                signal_sources[dim] = sources
                
        # Apply Corroboration Gate
        capped_scores, notes, gate_capped = apply_corroboration(scores, signal_sources)
        
        return {
            "scores": capped_scores,
            "gate_capped": gate_capped,
            "matched_evidence": {"exact": exact_res, "semantic": sem_res}
        }
