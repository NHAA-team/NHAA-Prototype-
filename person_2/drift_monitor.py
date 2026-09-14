def compute_override_rate(events: list, language: str, window_hours: int = 24) -> float:
    """
    Computes what fraction of actions for a given language within the time 
    window were overridden by the agent rather than confirmed as suggested.
    
    NOTE: This number is only meaningful once real call volume exists.
    A single test run will not produce a meaningful rate; this function
    serves as the proxy signal for the "silent accuracy drift" concern
    described in Section 2.11 of the solution document.
    """
    relevant_events = [e for e in events if e.get("language") == language]
    
    if not relevant_events:
        return 0.0
        
    overrides = sum(1 for e in relevant_events if e.get("action_state") == "overridden")
    return overrides / len(relevant_events)

if __name__ == "__main__":
    mock_events = [
        {"action_state": "agent_confirmed", "language": "hindi"},
        {"action_state": "overridden", "language": "hindi"},
        {"action_state": "agent_confirmed", "language": "english"}
    ]
    rate = compute_override_rate(mock_events, "hindi")
    assert rate == 0.5
    print("drift_monitor tests passed.")
