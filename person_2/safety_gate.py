from decision_aid import DecisionAidLayer, ActionType, ActionState
from consent import ConsentState, ConsentPurpose
from audit_log import AuditLog
from fake_pipeline import fake_risk_vector

class SafetyGateModule:
    def __init__(self):
        self.aid = DecisionAidLayer()
        self.logger = AuditLog()
        self.consent = ConsentState()

    def process_bucket_change(self, call_id: str, bucket: str, risk_scores: dict):
        actions = self.aid.suggest_for_bucket(call_id, bucket)
        self.logger.log("bucket_processed", call_id, {"bucket": bucket, "suggested": [a.value for a in actions]})
        return actions

    def handle_agent_action(self, call_id: str, action: ActionType, agent_id: str, caller_consent_given: bool):
        self.aid.agent_confirm(call_id, action, agent_id, caller_consent_given)
        new_state = self.aid.actions[(call_id, action)].state
        self.logger.log("agent_action", call_id, {"action": action.value, "state": new_state.value})

    def handle_senior_action(self, call_id: str, action: ActionType, senior_id: str):
        self.aid.senior_approve(call_id, action, senior_id)
        new_state = self.aid.actions[(call_id, action)].state
        self.logger.log("senior_action", call_id, {"action": action.value, "state": new_state.value})
