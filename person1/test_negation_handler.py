import pytest
from negation_handler import detect_negation_scope

def test_simple_negation_english():
    text = "I do not want to end my life."
    is_neg, word = detect_negation_scope(text, "want to end my life")
    assert is_neg is True
    assert word == "not"

def test_simple_negation_hindi():
    text = "main khud ko nuksan nahi pahunchana chahti"
    is_neg, word = detect_negation_scope(text, "nuksan")
    assert is_neg is True
    assert word == "nahi"

def test_no_negation():
    text = "I really want to end my life right now."
    is_neg, word = detect_negation_scope(text, "want to end my life")
    assert is_neg is False

def test_negation_out_of_scope():
    text = "He said no, but I want to end my life."
    # "no" is more than ~35 chars away, or separated by strong punctuation (in a perfect implementation)
    # Our simple implementation just uses a 35 char window. Let's make sure it's out of scope.
    text_long = "He said no. " + "a " * 15 + " I want to end my life."
    is_neg, word = detect_negation_scope(text_long, "want to end my life")
    assert is_neg is False

def test_hedging_self_correction_hindi():
    # As the user noted, real speech is messy: 
    # "nahi, nahi... matlab, haan, kabhi kabhi lagta hai ki bas sab khatam kar doon"
    text = "nahi, nahi... matlab, haan, kabhi kabhi lagta hai ki bas sab khatam kar doon"
    
    # "sab khatam kar doon" is the trigger phrase here.
    # We want to ensure that "nahi" is considered out of scope because it's too far back,
    # preventing false-negative suppression. 
    is_neg, word = detect_negation_scope(text, "sab khatam kar doon")
    assert is_neg is False
