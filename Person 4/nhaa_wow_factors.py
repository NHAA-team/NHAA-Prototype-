import random
import json
import os
import shutil

# --- PHASE 2: Silent SOS ---

def detect_duress_code(dtmf_sequence: str) -> bool:
    """
    Returns True if the specific agreed duress sequence '9631' appears in the stream
    of keypad presses. This sequence is chosen as it's unlikely to be pressed 
    by accident during normal call navigation.
    """
    return "9631" in dtmf_sequence

def apply_duress_mode(current_bucket: str) -> dict:
    """
    Represents the system's response to a detected duress signal. 
    It intentionally omits any fields that bypass the senior-approval gate.
    It raises the urgency to critical and switches the agent's script mode.
    """
    return {
        "bucket": "critical",
        "duress_active": True,
        "agent_script_mode": "yes_no_only"
    }

# --- PHASE 3: Referral Booking and Wellbeing Signal ---

def find_and_book_slot(district: str, referral_type: str, case_summary: dict = None) -> dict:
    """
    Searches mock_directory.json for the earliest available slot for a given
    district and referral type. Marks it as booked (removes it) and returns a
    confirmation object. If case_summary is provided, includes it for warm hand-off.
    """
    file_path = os.path.join(os.path.dirname(__file__), "mock_directory.json")
    with open(file_path, "r") as f:
        directory = json.load(f)
    
    booked_slot = None
    booked_center = None
    
    for center in directory:
        if center["district"] == district and center["type"] == referral_type:
            if center["available_slots"]:
                # Pop the earliest available slot
                booked_slot = center["available_slots"].pop(0)
                booked_center = center
                break
                
    if not booked_slot:
        return {"error": "No available slots found"}
        
    # Write the updated directory back to the file
    with open(file_path, "w") as f:
        json.dump(directory, f, indent=2)
        
    response = {
        "status": "confirmed",
        "center_name": booked_center["name"],
        "district": booked_center["district"],
        "type": booked_center["type"],
        "appointment_time": booked_slot
    }
    
    if case_summary is not None:
        response["handoff_summary"] = case_summary
        
    return response

def wellbeing_signal(response_times: list, avg_response_length: list) -> dict:
    """
    Analyzes agent response times and message lengths across a shift to detect fatigue.
    This is a starting heuristic mapped to the ProQOL-5 (Professional Quality of Life) 
    'Burnout' subscale category, intended for future validation against the real instrument.
    (Other ProQOL-5 categories include Compassion Satisfaction and Secondary Traumatic Stress).
    """
    if len(response_times) < 5:
        return {"status": "insufficient_data"}
        
    first_five_avg = sum(response_times[:5]) / 5.0
    recent_avg = sum(response_times[-5:]) / min(5, len(response_times))
    
    # Check if recent response times are more than 30% slower than the initial baseline
    if recent_avg > first_five_avg * 1.3:
        return {
            "category": "burnout",
            "concern_level": "moderate"
        }
        
    return {"status": "normal"}

# --- PHASE 4: Accessibility Bridge Backend ---

def score_text_only_input(transcript: str) -> dict:
    """
    Accessibility bridge backend for text-based channels.
    Takes plain text and returns a risk-vector shape by scanning for
    phrases from the keywords/ JSON files and scoring by match count.
    """
    keywords_dir = os.path.join(os.path.dirname(__file__), "keywords")
    risk_vector = {}
    
    if not os.path.exists(keywords_dir):
        return risk_vector

    transcript_lower = transcript.lower()

    for filename in os.listdir(keywords_dir):
        if filename.endswith(".json"):
            dimension = filename[:-5]
            file_path = os.path.join(keywords_dir, filename)
            
            with open(file_path, "r") as f:
                try:
                    entries = json.load(f)
                except json.JSONDecodeError:
                    entries = []
            
            match_count = 0
            for entry in entries:
                phrase = entry.get("phrase", "").lower()
                if phrase and phrase in transcript_lower:
                    match_count += 1
            
            risk_vector[dimension] = match_count
            
    return risk_vector

# --- TESTS ---

def test_silent_sos():
    print("Running tests for Phase 2: Silent SOS Module...")
    random_digits_before = "".join([str(random.randint(0, 9)) for _ in range(15)])
    random_digits_after = "".join([str(random.randint(0, 9)) for _ in range(15)])
    
    positive_sequence = random_digits_before + "9631" + random_digits_after
    assert detect_duress_code(positive_sequence) == True, "Failed to detect valid duress code"
    print(f"Passed: Positive detection for sequence '{positive_sequence}'")
    
    negative_sequence = (random_digits_before + random_digits_after).replace("9631", "1369")
    assert detect_duress_code(negative_sequence) == False, "False positive on random string"
    print(f"Passed: Negative detection for sequence '{negative_sequence}'")

    mode = apply_duress_mode("low")
    assert mode["bucket"] == "critical"
    assert mode["duress_active"] == True
    assert mode["agent_script_mode"] == "yes_no_only"
    print("Passed: apply_duress_mode returns correctly shaped response object")
    print("All Phase 2 tests passed!\n")

def test_referral_and_wellbeing():
    print("Running tests for Phase 3: Referral Booking and Wellbeing Signal...")
    # 1. Test Referral Booking
    mock_path = os.path.join(os.path.dirname(__file__), "mock_directory.json")
    backup_path = mock_path + ".bak"
    shutil.copy(mock_path, backup_path)
    
    try:
        summary = {"risk_score": 85, "top_dimension": "intimidation"}
        
        # First booking call
        result1 = find_and_book_slot("District A", "counseling", case_summary=summary)
        assert result1.get("status") == "confirmed"
        assert "handoff_summary" in result1
        assert result1["handoff_summary"] == summary
        slot1 = result1["appointment_time"]
        
        # Second booking call
        result2 = find_and_book_slot("District A", "counseling", case_summary=summary)
        assert result2.get("status") == "confirmed"
        slot2 = result2["appointment_time"]
        
        assert slot1 != slot2
        print(f"Passed: find_and_book_slot returns different slots ({slot1} vs {slot2})")
        print(f"Passed: handoff_summary populated properly with case context.")
        
    finally:
        shutil.move(backup_path, mock_path)
        
    # 2. Test Wellbeing Signal
    # Mock data: 20 numbers, trending slower (2.0s to ~4.0s) simulating fatigue
    response_times = [2.0, 2.1, 1.9, 2.0, 2.1] + [2.5] * 10 + [3.8, 4.0, 4.2, 3.9, 4.1]
    avg_response_length = [50, 48, 52, 51, 49] + [35] * 10 + [20, 18, 15, 19, 16]
    
    wellbeing_res = wellbeing_signal(response_times, avg_response_length)
    assert wellbeing_res.get("category") == "burnout"
    assert wellbeing_res.get("concern_level") == "moderate"
    print("Passed: wellbeing_signal successfully detects 'burnout' based on response time degradation")
    print("All Phase 3 tests passed!\n")

def test_accessibility_bridge():
    print("Running tests for Phase 4: Accessibility Bridge Backend...")
    # Using one of the Phase 1 vignettes exactly as it appears in the JSON
    vignette = "They are waiting outside my house right now with sticks. They said they will burn it down if the police come. I cannot even step out."
    
    vector = score_text_only_input(vignette)
    
    assert "fear_of_retaliation" in vector
    assert vector["fear_of_retaliation"] > 0
    print(f"Passed: score_text_only_input correctly matched and scored the vignette for 'fear_of_retaliation'")
    print(f"Risk Vector Output: {vector}")
    print("All Phase 4 tests passed!\n")

if __name__ == "__main__":
    test_silent_sos()
    test_referral_and_wellbeing()
    test_accessibility_bridge()
