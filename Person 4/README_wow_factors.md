# Person 4 - Wow-Factor Layer

This module provides the "Wow-Factor" extensions for the NHAA Trauma Triage System, as outlined in the standalone build specification. All deliverables are contained within the `nhaa_wow_factors.py` module and the accompanying `keywords/` and `mock_directory.json` datasets.

## Module: `nhaa_wow_factors.py`

This module contains five separately-callable functions across the different project phases. You can import these directly to integrate with the main pipeline.

### 1. `detect_duress_code(dtmf_sequence: str) -> bool`
Detects the agreed-upon Silent SOS duress sequence ("9631") within a stream of DTMF keypad presses.
- **Input:** A string representing the sequence of keypad presses (e.g., `"1234963145"`).
- **Returns:** A boolean `True` if the duress code is found, `False` otherwise.
- **Example Call:**
  ```python
  from nhaa_wow_factors import detect_duress_code
  is_duress = detect_duress_code("1239631789")
  # Returns: True
  ```

### 2. `apply_duress_mode(current_bucket: str) -> dict`
Generates the system response configuration when a duress signal is detected. It intentionally omits fields that would bypass senior-approval gates.
- **Input:** A string indicating the caller's current risk bucket (e.g., `"low"`, `"moderate"`).
- **Returns:** A dictionary updating the risk bucket to `"critical"`, activating duress mode, and shifting the agent script.
- **Example Call:**
  ```python
  from nhaa_wow_factors import apply_duress_mode
  config = apply_duress_mode("low")
  # Returns: {'bucket': 'critical', 'duress_active': True, 'agent_script_mode': 'yes_no_only'}
  ```

### 3. `find_and_book_slot(district: str, referral_type: str, case_summary: dict = None) -> dict`
Searches the `mock_directory.json` for an available counseling or legal aid slot in the specified district, books the earliest slot, and prepares a hand-off summary for the receiving counselor.
- **Input:**
  - `district` (str): The target district (e.g., `"District A"`).
  - `referral_type` (str): `"counseling"` or `"legal_aid"`.
  - `case_summary` (dict, optional): The case's risk-dimension summary.
- **Returns:** A dictionary containing the confirmed booking details and (if provided) the warm hand-off summary.
- **Example Call:**
  ```python
  from nhaa_wow_factors import find_and_book_slot
  summary = {"risk_score": 85, "top_dimension": "intimidation"}
  booking = find_and_book_slot("District A", "counseling", case_summary=summary)
  # Returns: {'status': 'confirmed', 'center_name': 'District A Counseling Center', 'district': 'District A', 'type': 'counseling', 'appointment_time': '2026-09-09T10:00:00', 'handoff_summary': {'risk_score': 85, 'top_dimension': 'intimidation'}}
  ```

### 4. `wellbeing_signal(response_times: list, avg_response_length: list) -> dict`
Analyzes agent response times and message lengths across a shift to detect fatigue, functioning as a heuristic for the ProQOL-5 "Burnout" subscale.
- **Input:**
  - `response_times` (list of floats): Array of response times in seconds across the shift.
  - `avg_response_length` (list of ints): Array of average message lengths across the shift.
- **Returns:** A dictionary signaling fatigue/burnout if response times trend >30% slower than the first 5 calls.
- **Example Call:**
  ```python
  from nhaa_wow_factors import wellbeing_signal
  times = [2.0, 2.1, 1.9, 2.0, 2.1, 3.8, 4.0, 4.2, 3.9, 4.1]
  lengths = [50, 48, 52, 51, 49, 20, 18, 15, 19, 16]
  alert = wellbeing_signal(times, lengths)
  # Returns: {'category': 'burnout', 'concern_level': 'moderate'}
  ```

### 5. `score_text_only_input(transcript: str) -> dict`
The Accessibility Bridge backend scoring function. Takes plain text input and computes a risk-vector shape by matching phrases against the keyword JSON vignettes.
- **Input:** A string containing the text transcript.
- **Returns:** A dictionary mapping risk dimensions (e.g., `"fear_of_retaliation"`) to their match count.
- **Example Call:**
  ```python
  from nhaa_wow_factors import score_text_only_input
  transcript = "They are waiting outside my house right now with sticks."
  risk_vector = score_text_only_input(transcript)
  # Returns: {'fear_of_retaliation': 1, 'intimidation': 0}
  ```
