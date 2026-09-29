# NHAA Trauma Triage System -- Safety Gate Module

This module implements the core safety and ethics architecture for the NHAA Trauma Triage System.
It strictly enforces the human-in-the-loop requirement for any irreversible or high-stakes action.

## Usage (For person1)

At merge time, your real pipeline should replace `fake_pipeline.py`. 
You interact with the Safety Gate through the `SafetyGateModule` interface in `safety_gate.py`.

### Example
```python
from safety_gate import SafetyGateModule
from decision_aid import ActionType

gate = SafetyGateModule()

# Process the risk vector output
actions = gate.process_bucket_change("call-id-123", risk_vector["bucket"], risk_vector["scores"])

# Handle an agent confirming an action
gate.handle_agent_action("call-id-123", ActionType.police_intervention, "agent-007", True)

# Handle the senior reviewer approving it
gate.handle_senior_action("call-id-123", ActionType.police_intervention, "senior-555")
```

## Adversarial Testing Proof

We ran extensive adversarial tests to ensure the gate holds against bypassed methods.
The results confirm every bypass attempt fails safely.

```text
Phase 3 Flow Simulation Passed Successfully!
All adversarial tests passed. Known limitation: Python cannot fully prevent direct assignment to _state if a developer maliciously bypasses conventions, but the class interface itself prevents invalid transitions.
```

**Known Python Language Limitations**: 
As part of Test 4, we confirmed that Python cannot strictly enforce private variables. A malicious developer can still technically write `record._state = ActionState.executed`. However, the class interface is designed to make this very awkward and unnatural. Through standard methods (`agent_confirm`, `senior_approve`), this bypass is impossible.
