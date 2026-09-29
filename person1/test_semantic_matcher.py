import pytest
from semantic_matcher import SemanticMatcher

@pytest.fixture(scope="module")
def matcher():
    return SemanticMatcher()

def test_semantic_match_self_harm(matcher):
    # This phrase isn't in the exact keywords, but is semantically very close to "I want to end my life"
    text = "im going to kill myself tonight"
    result = matcher.match(text)
    
    assert "self_harm_risk" in result
    matches = result["self_harm_risk"]
    assert len(matches) > 0
    assert "semantically similar to" in matches[0]["evidence"]

def test_semantic_match_benign(matcher):
    # This should not trigger any high similarity matches
    text = "The weather is really nice today, let's go for a walk in the park."
    result = matcher.match(text)
    
    # We should have no matches or only very low-confidence matches that didn't pass the threshold
    assert not any(len(matches) > 0 for matches in result.values())

def test_exact_match_ignored_by_semantic_matcher(matcher):
    # If the text contains the EXACT keyword, the semantic matcher shouldn't duplicate it.
    # We test this by sending an exact keyword string.
    text = "I want to end my life"
    result = matcher.match(text)
    
    # It shouldn't return this as a soft match because it's an exact substring
    if "self_harm_risk" in result:
        for match in result["self_harm_risk"]:
            assert match["matched_against"] != "i want to end my life"
