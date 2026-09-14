# NHAA Frontier Layer

This module (`nhaa_frontier.py`) contains four frontier capabilities for the NHAA Trauma Triage System:

## 1. Cross-Call Pattern Linkage
- `check_pattern_correlation(new_case: dict, recent_cases: list) -> dict`
  Compares a new case against recent cases using safe categorical features to identify potential linked patterns without using raw transcript text or audio. If a similarity score above 0.6 is found, the cases are flagged.

## 2. Live Interview Coach
- `generate_coaching_cue(risk_vector: dict, recent_silence_event: dict, recent_question_type: str) -> str`
  Provides live, real-time coaching cues to agents. For example, it suggests to "Let this silence continue -- do not fill it." during extended mid-sentence pauses, or suggests "Consider an open-ended question here." if there are high risk factors for intimidation or fear of retaliation during a yes/no question.

## 3. Outcome Feedback Loop
- `init_db(db_path=":memory:")`
  Initializes an SQLite database for tracking case outcomes.
- `schedule_followup(case_id: str, weeks_ahead: int = 3)`
  Schedules a followup check for a given case ID.
- `record_outcome(case_id: str, response_text: str)`
  Records the caller's actual outcome feedback, marking it for human review.
- `get_pending_human_reviews() -> list`
  Retrieves a queue of cases where outcomes have been recorded but not yet reviewed by a human professional.

## 4. The ASHA Bridge Software Layer
- `prepare_asha_handoff(case_id: str, action_state: dict, case_summary: dict) -> dict`
  Validates that a high-risk case has successfully passed a senior approval gate before generating a secure handoff object for an ASHA community health worker.
- `mock_asha_receiving_system(handoff: dict) -> None`
  A mock stand-in function representing the receiving system, which safely logs the generated handoff.

## Honesty Note

The Cross-Call Pattern Linkage, Live Interview Coach, and Outcome Feedback Loop modules in this package are complete, real, working software. The ASHA Physical Safety Bridge module is also complete, real, working software for everything up to and including the handoff object -- what it does not include, because it cannot be built in code, is an actual live connection to a real ASHA worker network, which requires a state-level institutional partnership outside this project's scope. This module is fully ready to connect to such a partnership the moment one exists.
