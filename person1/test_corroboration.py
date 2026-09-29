import pytest
from corroboration_gate import apply_corroboration

def test_single_signal_caps_at_moderate():
    scores = {"self_harm_risk": 0.90}
    signal_sources = {
        "self_harm_risk": {
            "lexical": True,
            "semantic": False,
            "silence": False,
            "acoustic": False
        }
    }
    
    capped, notes = apply_corroboration(scores, signal_sources)
    
    assert capped["self_harm_risk"] == 0.50
    assert "single-signal only" in notes["self_harm_risk"]

def test_corroborated_signals_allow_critical():
    scores = {"intimidation": 0.90}
    signal_sources = {
        "intimidation": {
            "lexical": True,
            "semantic": True,
            "silence": False,
            "acoustic": False
        }
    }
    
    capped, notes = apply_corroboration(scores, signal_sources)
    
    assert capped["intimidation"] == 0.90
    assert "corroborated by 2" in notes["intimidation"]

def test_silence_corroboration():
    scores = {"dissociation": 0.90}
    signal_sources = {
        "dissociation": {
            "lexical": True,
            "semantic": False,
            "silence": True,
            "acoustic": False
        }
    }
    
    capped, notes = apply_corroboration(scores, signal_sources)
    
    assert capped["dissociation"] == 0.90
    assert "corroborated by 2" in notes["dissociation"]
