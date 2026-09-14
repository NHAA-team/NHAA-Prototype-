from fake_pipeline import fake_risk_vector
from consent import ConsentState, ConsentPurpose
from decision_aid import DecisionAidLayer, ActionType, ActionState
from audit_log import AuditLog

def simulate_flow():
    # Setup
    consent = ConsentState()
    aid = DecisionAidLayer()
    logger = AuditLog()
    call_id = "test-critical-call"
    agent_id = "agent-x"
    senior_id = "senior-y"
    
    # 1. Consent is granted
    consent.grant(ConsentPurpose.recording)
    consent.grant(ConsentPurpose.ai_analysis)
    logger.log("consent_granted", call_id, {"purposes": ["recording", "ai_analysis"]})
    
    # 2. Critical bucket is reached
    risk_data = fake_risk_vector("critical")
    logger.log("risk_vector_generated", call_id, risk_data)
    
    # 3. All five actions are suggested
    suggested_actions = aid.suggest_for_bucket(call_id, risk_data["bucket"])
    assert len(suggested_actions) == 5
    logger.log("actions_suggested", call_id, {"actions": [a.value for a in suggested_actions]})
    
    # 4. Counseling is agent-confirmed and executed
    caller_consent = True
    aid.agent_confirm(call_id, ActionType.counseling_referral, agent_id, caller_consent)
    assert aid.actions[(call_id, ActionType.counseling_referral)].state == ActionState.executed
    logger.log("action_agent_confirmed", call_id, {"action": "counseling_referral", "state": "executed"})
    
    # 5. police_intervention is agent-confirmed (moves to awaiting_senior)
    aid.agent_confirm(call_id, ActionType.police_intervention, agent_id, caller_consent)
    assert aid.actions[(call_id, ActionType.police_intervention)].state == ActionState.awaiting_senior
    logger.log("action_agent_confirmed", call_id, {"action": "police_intervention", "state": "awaiting_senior"})
    
    # 6. then senior-approved (moves to executed)
    aid.senior_approve(call_id, ActionType.police_intervention, senior_id)
    assert aid.actions[(call_id, ActionType.police_intervention)].state == ActionState.executed
    logger.log("action_senior_approved", call_id, {"action": "police_intervention", "state": "executed"})
    
    # 7. Confirm verify_chain returns True
    assert logger.verify_chain(call_id) is True
    print("Phase 3 Flow Simulation Passed Successfully!")

if __name__ == "__main__":
    simulate_flow()
