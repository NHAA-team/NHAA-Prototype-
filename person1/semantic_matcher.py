import os
import json
import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util

class SemanticMatcher:
    def __init__(self, keywords_dir=None):
        # We use a fixed threshold to emulate the original logic before classifiers
        self.threshold = 0.70
        self.partial_threshold = 0.55
        
        self.embedding_model = SentenceTransformer('l3cube-pune/hindi-sentence-bert-nli')
        self.reference_embeddings = {}
        self.reference_phrases = {}
        self.reference_weights = {}
        
        self.mean_vector = None
        
        if keywords_dir:
            self._load_keywords(keywords_dir)

    def _load_keywords(self, kw_dir):
        all_phrases = []
        for fname in os.listdir(kw_dir):
            if fname.endswith('.json'):
                dim = fname.replace('.json', '')
                with open(os.path.join(kw_dir, fname), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    phrases = [item['phrase'].lower().strip() for item in data]
                    weights = [item.get('weight', 1.0) for item in data]
                    if phrases:
                        self.reference_phrases[dim] = phrases
                        self.reference_weights[dim] = weights
                        all_phrases.extend(phrases)
                        
        clean_negatives = [
            "aaj kal mausam bahut ajeeb ho gaya hai",
            "Bhai, weekend plan kya hai?",
            "mera bhai ki shadi fix ho gayi hai",
            "aaj raat ko dinner me kya banega?",
            "kal mujhe bank jana padega",
            "office me aaj bahut zyada kaam tha",
            "traffic ki wajah se aaj office pahunchne me late ho gaya",
            "Petrol prices kal se fir badh gaye hai",
            "aaj sabzi mandi me bhindi itni mehengi thi",
            "meri watch ki battery khatam ho gayi hai",
            "I need to renew my car insurance",
            "I ordered a pizza half an hour ago",
            "Can you recommend a good book",
            "I'm thinking of joining a pottery class",
            "The museum exhibition on ancient Egypt opens next Tuesday"
        ]
        
        all_phrases.extend([cn.lower() for cn in clean_negatives])
        
        if all_phrases:
            all_embs = self.embedding_model.encode(all_phrases, convert_to_tensor=True)
            self.mean_vector = torch.mean(all_embs, dim=0, keepdim=True)
            
            for dim, phrases in self.reference_phrases.items():
                embs = self.embedding_model.encode(phrases, convert_to_tensor=True)
                centered_embs = embs - self.mean_vector
                self.reference_embeddings[dim] = centered_embs

    def match(self, transcript_text: str) -> dict:
        result = {}
        text_lower = transcript_text.lower().strip()
        if not text_lower:
            return result
            
        import re
        clean_text = re.sub(r'[^\w\s]', '', text_lower)
        words = set(clean_text.split())
        hi_words = {'hai', 'ki', 'ke', 'ko', 'mein', 'aur', 'se', 'bhi', 'toh', 'ye', 'wo', 'tha', 'thi', 'hu', 'hoon', 'kya', 'mujhe', 'mera', 'mere', 'ka', 'kuch', 'nahi'}
        is_hindi = bool(words.intersection(hi_words))
        
        if is_hindi:
            return result # Fall back to exact keyword matching only in RiskScorer
            
        emb = self.embedding_model.encode([text_lower], convert_to_tensor=True)
        if self.mean_vector is not None:
            emb = emb - self.mean_vector
        
        for dim, ref_embs in self.reference_embeddings.items():
            cos_scores = util.cos_sim(emb, ref_embs)[0]
            best_idx = int(cos_scores.argmax())
            best_score = float(cos_scores[best_idx])
            best_weight = self.reference_weights[dim][best_idx]
            
            if best_weight < 0:
                continue # Hard negative matched best, suppress
                
            if best_score >= self.partial_threshold:
                result[dim] = [{
                    "matched_against": self.reference_phrases[dim][best_idx],
                    "similarity": round(best_score, 4),
                    "evidence": "semantic_similarity"
                }]
                
        return result
