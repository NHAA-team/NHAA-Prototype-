import re

def detect_negation_scope(transcript: str, match_phrase: str, language: str = "en", is_semantic_sentence: bool = False) -> tuple[bool, str]:
    """
    Checks for negation words/phrases within a small window (~35 chars)
    BEFORE and AFTER the matched phrase in the transcript.
    
    Hindi/Hinglish negation often follows the verb/noun ("nuksan nahi pahunchana"),
    so we must check both directions.
    
    Returns (True, negation_word) if negated, else (False, "").
    """
    transcript = transcript.lower()
    match_phrase = match_phrase.lower()
    
    # Find all occurrences of the phrase
    starts = [m.start() for m in re.finditer(re.escape(match_phrase), transcript)]
    if not starts:
        return False, ""
        
    match_start = starts[0]
    match_end = match_start + len(match_phrase)
    
    # Extract the context window before the match (~35 characters)
    window_start = max(0, match_start - 35)
    context_before = transcript[window_start:match_start]
    
    # Extract the context window after the match (~35 characters)
    context_after = transcript[match_end:match_end + 35]
    
    # Define negation words
    # Define negation words (with AND without apostrophes — speech recognition often drops them)
    negations_en = [
        "not", "never", "no longer", "cannot", "no",
        "don't", "doesn't", "isn't", "won't", "didn't", "can't", "wasn't", "weren't", "haven't", "hasn't",
        "dont", "doesnt", "isnt", "wont", "didnt", "cant", "wasnt", "werent", "havent", "hasnt",
    ]
    negations_hi = ["nahi", "nahin", "kabhi nahi", "mat", "naa", "bilkul nahi", "na", "नहीं", "मत", "ना", "कभी नहीं"]
    
    negations = negations_en + negations_hi
    
    # Sort by length descending to match longest phrases first (e.g. "no longer" before "no")
    negations.sort(key=len, reverse=True)
    
    # Check BEFORE the match
    for neg in negations:
        pattern = r'\b' + re.escape(neg) + r'\b'
        
        # If it's a semantic sentence, checking inside the sentence itself is often necessary
        # because the matched phrase is the entire sentence.
        if is_semantic_sentence and re.search(pattern, match_phrase):
            return True, neg
            
        if re.search(pattern, context_before):
            return True, neg
            
    # Check AFTER the match (important for Hindi SOV word order)
    for neg in negations:
        pattern = r'\b' + re.escape(neg) + r'\b'
        if re.search(pattern, context_after):
            return True, neg
    
    return False, ""
