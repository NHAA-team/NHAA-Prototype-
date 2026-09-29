def apply_corroboration(scores: dict, signal_sources: dict) -> tuple[dict, dict, set]:
    """
    Applies multi-signal corroboration logic to dimension scores.
    
    Rules:
    1. A dimension can only exceed 0.50 if at least TWO independent signal types
       agree AND at least one is a full hit (weight >= 1.0).
    2. Dimensions with ONLY semantic evidence (no lexical/keyword match) are 
       marked as gate_capped — their scores are excluded from the SVI weighted
       sum and breadth multiplier because semantic-only signals on multilingual
       text are too noisy to drive severity scoring.
    3. Dimensions with a lexical (keyword) match are NEVER gate_capped — keyword
       matches are precise, direct evidence.
    """
    capped_scores = {}
    notes = {}
    gate_capped = set()
    
    for dim, score in scores.items():
        if score <= 0.0:
            capped_scores[dim] = score
            continue
            
        sources = signal_sources.get(dim, {})
        has_lexical = sources.get("lexical", 0) > 0
        has_semantic = sources.get("semantic", 0) > 0
        has_silence = sources.get("silence", 0) > 0
        
        active_signals = sum(1 for v in sources.values() if v > 0)
        has_full_hit = any(v >= 1.0 for v in sources.values())
        
        # Gate-capping: only for semantic-only dimensions (no keyword backup)
        if not has_lexical and not has_silence:
            gate_capped.add(dim)
            notes[dim] = "semantic-only — excluded from SVI (needs keyword corroboration)"
        
        # Score capping: dimensions above 0.50 need corroboration to stay there
        if score > 0.50:
            if active_signals < 2 or not has_full_hit:
                capped_scores[dim] = 0.50
                if dim not in notes:
                    notes[dim] = "single-signal — capped at 0.50 (needs corroboration for higher)"
            else:
                capped_scores[dim] = score
                if dim not in notes:
                    notes[dim] = f"corroborated by {active_signals} signals (including full hit)"
        else:
            capped_scores[dim] = score
            
    return capped_scores, notes, gate_capped

