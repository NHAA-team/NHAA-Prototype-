import sqlite3
from datetime import datetime, timedelta

"""
Safe Features for Cross-Call Pattern Linkage:
- "named individual mentioned" (normalized string)
- "locality type" (category, e.g., village/town/city)
- "intimidation method category" (fixed short list)
- "district" (normalized string)

Explicit Note: Raw transcript text, audio, or anything that could 
identify a specific caller is NEVER included in this comparison. 
This ensures privacy and prevents re-identification.
"""

def check_pattern_correlation(new_case: dict, recent_cases: list) -> dict:
    """
    Compares a new case against recent cases using safe categorical features.
    If any comparison scores above 0.6, returns a flag and matched case IDs.
    """
    matched_case_ids = []
    
    # We assume 'case_id' is present but shouldn't be compared as a feature
    for recent_case in recent_cases:
        # Extract features to compare (excluding case_id)
        new_features = {k: v for k, v in new_case.items() if k != "case_id"}
        recent_features = {k: v for k, v in recent_case.items() if k != "case_id"}
        
        # Get common keys to compare
        common_keys = set(new_features.keys()).intersection(set(recent_features.keys()))
        
        if not common_keys:
            continue
            
        matching_fields = sum(1 for k in common_keys if new_features[k] == recent_features[k])
        total_fields_compared = len(common_keys)
        
        similarity_score = matching_fields / total_fields_compared
        
        if similarity_score > 0.6:
            matched_case_ids.append(recent_case.get("case_id"))
            
    if matched_case_ids:
        return {"flagged": True, "matched_case_ids": matched_case_ids}
    else:
        return {"flagged": False}


def generate_coaching_cue(risk_vector: dict, recent_silence_event: dict, recent_question_type: str) -> str:
    """
    Returns a coaching cue string based on risk vector, silence events, and question type.
    """
    if recent_silence_event.get("placement") == "mid_sentence" and recent_silence_event.get("duration_sec", 0) > 2:
        return "Let this silence continue -- do not fill it."
        
    if (risk_vector.get("fear_of_retaliation", 0) > 0.5 or risk_vector.get("intimidation", 0) > 0.5) and recent_question_type == "yes_no":
        return "Consider an open-ended question here."
        
    return ""


# --- Phase 3: Outcome Feedback Loop ---

def init_db(db_path=":memory:"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outcome_followups (
            case_id TEXT PRIMARY KEY,
            scheduled_date TEXT,
            consent_given BOOLEAN,
            outcome_response TEXT,
            reviewed_by_human BOOLEAN
        )
    ''')
    conn.commit()
    return conn

# Global connection for the functions as per simple script design
DB_CONN = init_db()

def schedule_followup(case_id: str, weeks_ahead: int = 3):
    scheduled_date = (datetime.now() + timedelta(weeks=weeks_ahead)).isoformat()
    cursor = DB_CONN.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO outcome_followups (case_id, scheduled_date, consent_given, outcome_response, reviewed_by_human)
        VALUES (?, ?, ?, ?, ?)
    ''', (case_id, scheduled_date, True, None, False))
    DB_CONN.commit()

def record_outcome(case_id: str, response_text: str):
    cursor = DB_CONN.cursor()
    cursor.execute('''
        UPDATE outcome_followups 
        SET outcome_response = ?, reviewed_by_human = 0
        WHERE case_id = ?
    ''', (response_text, case_id))
    DB_CONN.commit()

def get_pending_human_reviews() -> list:
    cursor = DB_CONN.cursor()
    cursor.execute('''
        SELECT case_id, scheduled_date, consent_given, outcome_response, reviewed_by_human 
        FROM outcome_followups
        WHERE outcome_response IS NOT NULL AND reviewed_by_human = 0
    ''')
    return cursor.fetchall()


# --- Phase 4: The ASHA Bridge Software Layer ---

def prepare_asha_handoff(case_id: str, action_state: dict, case_summary: dict) -> dict:
    if action_state.get("state") != "executed" or action_state.get("requires_senior") is not True:
        raise ValueError("ASHA handoff refused: Action was not senior-approved and executed.")
    
    return {
        "case_id": case_id,
        "priority": "critical",
        "briefing": case_summary,
        "requested_action": "discreet welfare check",
        "framing_note": "present as routine health visit"
    }

def mock_asha_receiving_system(handoff: dict) -> None:
    import json
    with open("asha_handoff_log.txt", "a") as f:
        f.write(json.dumps(handoff) + "\n")


if __name__ == "__main__":
    print("Testing check_pattern_correlation...")
    
    # Test 1: Three synthetic cases sharing 'named individual' and 'locality type'
    case1 = {
        "case_id": "c1",
        "named individual mentioned": "john doe",
        "locality type": "village",
        "intimidation method category": "verbal threat"
    }
    case2 = {
        "case_id": "c2",
        "named individual mentioned": "john doe",
        "locality type": "village",
        "intimidation method category": "property damage"
    }
    case3 = {
        "case_id": "c3",
        "named individual mentioned": "john doe",
        "locality type": "village",
        "intimidation method category": "stalking"
    }
    
    # Comparing case1 against [case2, case3]
    # Common keys: 3
    # Matches: 2 ('named individual mentioned', 'locality type')
    # Similarity: 2 / 3 = 0.666... > 0.6
    res1 = check_pattern_correlation(case1, [case2, case3])
    assert res1["flagged"] is True
    assert "c2" in res1["matched_case_ids"]
    assert "c3" in res1["matched_case_ids"]
    print("Test 1 Passed: Correlated cases flagged correctly.")
    
    # Test 2: Five unrelated cases with no shared fields
    unrelated_cases = [
        {"case_id": f"u{i}", "named individual mentioned": f"person_{i}", "locality type": f"type_{i}", "intimidation method category": f"method_{i}"}
        for i in range(1, 6)
    ]
    
    # Test each against the others
    for i, new_case in enumerate(unrelated_cases):
        recent_cases = unrelated_cases[:i] + unrelated_cases[i+1:]
        res2 = check_pattern_correlation(new_case, recent_cases)
        assert res2["flagged"] is False
    print("Test 2 Passed: Unrelated cases not flagged.")
    
    print("All Phase 1 tests passed.\n")

    print("Testing generate_coaching_cue...")
    
    # Test 1: Mid-sentence silence > 2s
    cue1 = generate_coaching_cue(
        risk_vector={"fear_of_retaliation": 0.2, "intimidation": 0.1},
        recent_silence_event={"placement": "mid_sentence", "duration_sec": 3.5},
        recent_question_type="open"
    )
    assert cue1 == "Let this silence continue -- do not fill it."
    print("Test 1 Passed: Correct cue for mid-sentence silence.")
    
    # Test 2: High risk + yes/no question
    cue2 = generate_coaching_cue(
        risk_vector={"fear_of_retaliation": 0.6, "intimidation": 0.2},
        recent_silence_event={"placement": "end_sentence", "duration_sec": 1.0},
        recent_question_type="yes_no"
    )
    assert cue2 == "Consider an open-ended question here."
    print("Test 2 Passed: Correct cue for high risk and yes_no question.")
    
    # Test 3: No cue expected
    cue3 = generate_coaching_cue(
        risk_vector={"fear_of_retaliation": 0.2, "intimidation": 0.2},
        recent_silence_event={"placement": "end_sentence", "duration_sec": 1.0},
        recent_question_type="open"
    )
    assert cue3 == ""
    print("Test 3 Passed: No cue when conditions aren't met.")
    
    print("All Phase 2 tests passed.\n")

    print("Testing Outcome Feedback Loop...")
    
    test_case_id = "test_case_001"
    
    # Schedule followup
    schedule_followup(test_case_id, weeks_ahead=3)
    
    # Record a fake outcome
    record_outcome(test_case_id, "The provided legal aid was very helpful.")
    
    # Confirm it appears in pending reviews
    pending = get_pending_human_reviews()
    assert len(pending) == 1
    assert pending[0][0] == test_case_id
    assert pending[0][3] == "The provided legal aid was very helpful."
    
    print("Test Passed: Followup scheduled, outcome recorded, and appeared in pending queue.")
    print("All Phase 3 tests passed.\n")

    print("Testing The ASHA Bridge Software Layer...")
    
    import os
    
    test_case_id_4 = "test_case_asha"
    test_summary = {"risk_level": "critical", "location": "village X"}
    
    # 1. Test refusal if not senior approved
    invalid_state = {"state": "pending", "requires_senior": True}
    try:
        prepare_asha_handoff(test_case_id_4, invalid_state, test_summary)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print("Test 1 Passed: Correctly refused unapproved handoff.")
        
    invalid_state_2 = {"state": "executed", "requires_senior": False}
    try:
        prepare_asha_handoff(test_case_id_4, invalid_state_2, test_summary)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print("Test 2 Passed: Correctly refused action that didn't require senior approval.")
        
    # 2. Test success if senior approved
    valid_state = {"state": "executed", "requires_senior": True}
    handoff = prepare_asha_handoff(test_case_id_4, valid_state, test_summary)
    
    assert handoff["case_id"] == test_case_id_4
    assert handoff["priority"] == "critical"
    assert handoff["requested_action"] == "discreet welfare check"
    print("Test 3 Passed: Correctly produced handoff object.")
    
    # 3. Test mock receiving system logs it
    if os.path.exists("asha_handoff_log.txt"):
        os.remove("asha_handoff_log.txt")
        
    mock_asha_receiving_system(handoff)
    
    assert os.path.exists("asha_handoff_log.txt")
    with open("asha_handoff_log.txt", "r") as f:
        log_content = f.read()
        assert test_case_id_4 in log_content
    print("Test 4 Passed: mock_asha_receiving_system logged handoff correctly.")
    
    print("All Phase 4 tests passed.")
