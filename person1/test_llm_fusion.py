import pytest
from llm_fusion import LLMFusionLayer

def test_disabled_by_default():
    fusion = LLMFusionLayer()
    assert fusion.enabled is False
    
    rules_scores = {"self_harm_risk": 0.5}
    fused, agrees = fusion.fuse("I am sad", rules_scores)
    assert fused == rules_scores
    assert agrees is False

def test_override_rule_mocked(monkeypatch):
    fusion = LLMFusionLayer(enabled=True, api_key="fake")
    
    # Mock the openai call to return a lower score
    class MockMessage:
        content = '{"self_harm_risk": 0.2, "depression": 0.9}'
    class MockChoice:
        message = MockMessage()
    class MockResponse:
        choices = [MockChoice()]
        
    class MockCompletions:
        def create(self, **kwargs):
            return MockResponse()
    class MockChat:
        completions = MockCompletions()
    class MockClient:
        def __init__(self, **kwargs):
            self.chat = MockChat()
            
    import openai
    monkeypatch.setattr(openai, "OpenAI", MockClient)
    
    rules_scores = {"self_harm_risk": 0.9, "depression": 0.0}
    fused, agrees = fusion.fuse("I want to die", rules_scores)
    
    # self_harm_risk should stay 0.9 because LLM cannot lower it
    assert fused["self_harm_risk"] == 0.9
    # depression should become 0.9 from LLM
    assert fused["depression"] == 0.9
    # They disagreed heavily (0.9 vs 0.2)
    assert agrees is False
