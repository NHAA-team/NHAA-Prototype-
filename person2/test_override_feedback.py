import sqlite3
import pytest
from decision_aid import DecisionAidLayer, ActionType, ActionState

def test_override_creates_review_row():
    aid = DecisionAidLayer()
    call_id = "test_override_1"
    
    # Setup: suggest actions for a critical call
    aid.suggest_for_bucket(call_id, "critical")
    
    # Override with dimension scores
    dimension_scores = {
        "self_harm_risk": 0.90,
        "intimidation": 0.75,
        "acute_distress": 0.60
    }
    
    aid.agent_override(
        call_id, 
        ActionType.emergency_escalation, 
        "agent_1", 
        "Caller seems calm now, risk has subsided",
        dimension_scores_at_time=dimension_scores
    )
    
    # Verify the action is overridden
    assert aid.actions[(call_id, ActionType.emergency_escalation)].state == ActionState.overridden
    
    # Verify rows were written to the pending_calibration_review table
    cursor = aid._conn.cursor()
    cursor.execute("SELECT call_id, dimension, ai_score, agent_override_reason, reviewed FROM pending_calibration_review WHERE call_id = ?", (call_id,))
    rows = cursor.fetchall()
    
    assert len(rows) == 3  # One row per dimension
    
    # Check that the rows contain the correct data
    dims_found = {row[1] for row in rows}
    assert dims_found == {"self_harm_risk", "intimidation", "acute_distress"}
    
    for row in rows:
        assert row[0] == call_id
        assert row[3] == "Caller seems calm now, risk has subsided"
        assert row[4] == 0  # reviewed == 0 (not yet reviewed)

def test_override_schema():
    aid = DecisionAidLayer()
    
    cursor = aid._conn.cursor()
    cursor.execute("PRAGMA table_info(pending_calibration_review)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    assert "call_id" in columns
    assert "dimension" in columns
    assert "ai_score" in columns
    assert "agent_override_reason" in columns
    assert "reviewed" in columns
    assert "timestamp" in columns

def test_override_without_scores():
    # Backward compat: calling agent_override WITHOUT dimension_scores should NOT crash
    aid = DecisionAidLayer()
    call_id = "test_override_2"
    
    aid.suggest_for_bucket(call_id, "high")
    aid.agent_override(call_id, ActionType.legal_aid, "agent_1", "Not needed")
    
    assert aid.actions[(call_id, ActionType.legal_aid)].state == ActionState.overridden
    
    # No rows should have been written
    cursor = aid._conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pending_calibration_review WHERE call_id = ?", (call_id,))
    count = cursor.fetchone()[0]
    
    assert count == 0
