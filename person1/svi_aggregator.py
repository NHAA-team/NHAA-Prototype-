class SVIAggregator:
    def __init__(self):
        self.previous_smoothed_score = None
        
    def process(self, risk_scores):
        weights = {
            "self_harm_risk": 0.30,
            "fear_of_retaliation": 0.22,
            "acute_distress": 0.18,
            "dissociation": 0.14,
            "chronic_trauma_indicators": 0.10,
            "social_isolation": 0.06,
            "depression": 0.0,
            "intimidation": 0.0
        }
        
        new_raw_score = 0.0
        for dim, weight in weights.items():
            score = risk_scores.get(dim, 0.0)
            new_raw_score += score * weight * 100
            
        new_raw_score = min(100.0, max(0.0, new_raw_score))
        
        if self.previous_smoothed_score is None:
            smoothed = new_raw_score
        else:
            smoothed = 0.55 * new_raw_score + 0.45 * self.previous_smoothed_score
            
        self.previous_smoothed_score = smoothed
        
        if smoothed <= 25:
            bucket = "low"
        elif smoothed <= 50:
            bucket = "moderate"
        elif smoothed <= 75:
            bucket = "high"
        else:
            bucket = "critical"
            
        return {
            "value": round(smoothed, 2),
            "bucket": bucket
        }

if __name__ == "__main__":
    aggregator = SVIAggregator()
    
    scores_1 = {"self_harm_risk": 0.0, "acute_distress": 0.5} 
    scores_2 = {"self_harm_risk": 0.5, "acute_distress": 0.5, "fear_of_retaliation": 0.5} 
    scores_3 = {"self_harm_risk": 1.0, "acute_distress": 1.0, "fear_of_retaliation": 1.0, "dissociation": 1.0} 
    
    svi_1 = aggregator.process(scores_1)
    print("Call 1:", svi_1)
    
    svi_2 = aggregator.process(scores_2)
    print("Call 2:", svi_2)
    
    svi_3 = aggregator.process(scores_3)
    print("Call 3:", svi_3)
    
    assert svi_1["value"] < svi_2["value"] < svi_3["value"]
    print("Test passed: SVI climbed realistically with EMA smoothing.")
