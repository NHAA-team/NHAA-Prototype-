import json
import os
import pytest
from risk_scorer import RiskScorer

@pytest.fixture(scope="module")
def scorer():
    return RiskScorer()

def test_adversarial_vignettes(scorer):
    filepath = os.path.join(os.path.dirname(__file__), "adversarial_vignettes.json")
    with open(filepath, "r", encoding="utf-8") as f:
        vignettes = json.load(f)
        
    for idx, v in enumerate(vignettes):
        result = scorer.process(v["text"], [])
        
        target_dim = v["target_dimension"]
        expected_fire = v["expected_fire"]
        actual_score = result["scores"].get(target_dim, 0.0)
        
        # self_harm_risk and intimidation are penalized, not suppressed to 0
        # So they will still "fire" (score > 0.0), but their confidence will be capped at 0.20
        mech = v["expected_mechanism"]
        
        if mech == "negation-suppressed" and target_dim in ["self_harm_risk", "intimidation"]:
            assert actual_score <= 0.20, f"Vignette {idx} failed: High stakes should be penalized to <= 0.20"
            assert result["confidence"].get(target_dim, 0.0) <= 0.20, f"Vignette {idx} failed: Confidence should be low"
        elif mech in ["negation-suppressed", "semantic", "exact"]:
            did_fire = actual_score > 0.0
            assert did_fire == expected_fire, f"Vignette {idx} failed: {v['text']} - Expected {expected_fire}, got {did_fire} for {target_dim}"
