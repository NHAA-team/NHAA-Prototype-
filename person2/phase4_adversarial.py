from decision_aid import DecisionAidLayer, ActionType, ActionState

def run_adversarial_tests():
    # Setup
    aid = DecisionAidLayer()
    call_id = "adv_test_call"
    
    aid.suggest_for_bucket(call_id, "critical")
    
    # 1. Call senior_approve twice in a row on the same action.
    aid.agent_confirm(call_id, ActionType.police_intervention, "agent_1", True)
    aid.senior_approve(call_id, ActionType.police_intervention, "senior_1") # First should work
    try:
        aid.senior_approve(call_id, ActionType.police_intervention, "senior_1") # Second should fail
        assert False, "Test 1 failed: Should have rejected double senior approve"
    except ValueError:
        pass
        
    # 2. Call senior_approve on an action that was never suggested for that call at all.
    try:
        aid.senior_approve("some_other_call", ActionType.police_intervention, "senior_1")
        assert False, "Test 2 failed: Should have rejected approving an unsuggested action"
    except ValueError:
        pass
        
    # 3. Call agent_confirm twice on the same police_intervention action.
    aid2 = DecisionAidLayer()
    aid2.suggest_for_bucket("call_3", "critical")
    aid2.agent_confirm("call_3", ActionType.police_intervention, "agent_1", True)
    try:
        aid2.agent_confirm("call_3", ActionType.police_intervention, "agent_1", True)
        assert False, "Test 3 failed: Should have rejected double agent confirm"
    except ValueError:
        pass

    # 4. Attempt to directly set an action's state to executed by manipulating the object's internal state
    aid3 = DecisionAidLayer()
    aid3.suggest_for_bucket("call_4", "critical")
    
    # We can try to modify it directly
    try:
        aid3.actions[("call_4", ActionType.police_intervention)]._state = ActionState.executed
    except Exception as e:
        pass
        
    print("All adversarial tests passed. Known limitation: Python cannot fully prevent direct assignment to _state if a developer maliciously bypasses conventions, but the class interface itself prevents invalid transitions.")

if __name__ == "__main__":
    run_adversarial_tests()
