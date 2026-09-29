from enum import Enum
from typing import List
import sqlite3
import datetime
import json

class ActionType(Enum):
    counseling_referral = "counseling_referral"
    legal_aid = "legal_aid"
    police_intervention = "police_intervention"
    witness_protection = "witness_protection"
    emergency_escalation = "emergency_escalation"

class ActionState(Enum):
    suggested = "suggested"
    agent_confirmed = "agent_confirmed"
    awaiting_senior = "awaiting_senior"
    executed = "executed"
    rejected = "rejected"
    overridden = "overridden"

REQUIRES_SENIOR_SIGNOFF = {
    ActionType.police_intervention,
    ActionType.witness_protection,
    ActionType.emergency_escalation
}

class ActionRecord:
    def __init__(self, action_type: ActionType):
        self.action_type = action_type
        self._state = ActionState.suggested

    @property
    def state(self):
        return self._state

class DecisionAidLayer:
    def __init__(self, db_path=":memory:"):
        self.actions = {}
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        self._init_db()
        
    def _init_db(self):
        cursor = self._conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_calibration_review (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT,
                dimension TEXT,
                ai_score REAL,
                agent_override_reason TEXT,
                reviewed INTEGER,
                timestamp TEXT
            )
        ''')
        self._conn.commit()

    def log_override_for_review(self, call_id: str, action: ActionType, dimension_scores_at_time: dict, reason: str):
        cursor = self._conn.cursor()
        now = datetime.datetime.now(datetime.UTC).isoformat()
        
        # We log a row for each dimension score at the time of override
        for dim, score in dimension_scores_at_time.items():
            cursor.execute('''
                INSERT INTO pending_calibration_review (call_id, dimension, ai_score, agent_override_reason, reviewed, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (call_id, dim, score, reason, 0, now))
            
        self._conn.commit()


    def suggest_for_bucket(self, call_id: str, bucket: str) -> List[ActionType]:
        bucket = bucket.lower()
        if bucket == "low":
            actions = []
        elif bucket == "moderate":
            actions = [ActionType.counseling_referral]
        elif bucket == "high":
            actions = [ActionType.counseling_referral, ActionType.legal_aid]
        elif bucket == "critical":
            actions = list(ActionType)
        else:
            raise ValueError(f"Unknown bucket: {bucket}")
        
        for a in actions:
            self.actions[(call_id, a)] = ActionRecord(a)
            
        return actions

    def agent_confirm(self, call_id: str, action: ActionType, agent_id: str, caller_consent_given: bool):
        record = self.actions.get((call_id, action))
        if not record:
            raise ValueError("Action not suggested")
            
        if record._state != ActionState.suggested:
            raise ValueError(f"Cannot confirm action from state {record._state.value}")
        
        if action in REQUIRES_SENIOR_SIGNOFF:
            record._state = ActionState.awaiting_senior
        else:
            if caller_consent_given:
                record._state = ActionState.executed

    def senior_approve(self, call_id: str, action: ActionType, senior_id: str):
        record = self.actions.get((call_id, action))
        if not record:
            raise ValueError("Action not found")
            
        # The single most important line of code:
        if record._state != ActionState.awaiting_senior:
            raise ValueError(f"Cannot approve action. Current state is {record._state.value}, expected awaiting_senior.")
            
        record._state = ActionState.executed

    def senior_reject(self, call_id: str, action: ActionType, senior_id: str, reason: str):
        record = self.actions.get((call_id, action))
        if record:
            record._state = ActionState.rejected

    def agent_override(self, call_id: str, action: ActionType, agent_id: str, reason: str, dimension_scores_at_time: dict = None):
        record = self.actions.get((call_id, action))
        if record:
            record._state = ActionState.overridden
            if dimension_scores_at_time:
                self.log_override_for_review(call_id, action, dimension_scores_at_time, reason)

if __name__ == "__main__":
    aid = DecisionAidLayer()
    call_id = "test_call_1"
    
    # 1. Confirm a Critical-bucket call correctly suggests all five actions
    suggested = aid.suggest_for_bucket(call_id, "critical")
    assert len(suggested) == 5, "Expected all 5 actions to be suggested"
    
    # 2. Confirm calling agent_confirm on police_intervention moves it to awaiting_senior and NOT executed
    aid.agent_confirm(call_id, ActionType.police_intervention, "agent_1", True)
    assert aid.actions[(call_id, ActionType.police_intervention)].state == ActionState.awaiting_senior
    
    # 3. Confirm calling senior_approve on an action that is NOT in awaiting_senior state raises an error
    try:
        aid.senior_approve(call_id, ActionType.counseling_referral, "senior_1")
        assert False, "Expected ValueError when approving action not in awaiting_senior"
    except ValueError as e:
        assert "expected awaiting_senior" in str(e)
        
    # 4. Confirm calling senior_approve correctly on an action that IS in awaiting_senior moves it to executed
    aid.senior_approve(call_id, ActionType.police_intervention, "senior_1")
    assert aid.actions[(call_id, ActionType.police_intervention)].state == ActionState.executed
    
    print("All decision_aid tests passed.")
