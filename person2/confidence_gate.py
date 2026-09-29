def should_force_human_review(overall_confidence: float, bucket: str) -> bool:
    return overall_confidence < 0.5

if __name__ == "__main__":
    assert should_force_human_review(0.3, "High") is True
    assert should_force_human_review(0.8, "Critical") is False
    print("confidence_gate tests passed.")
