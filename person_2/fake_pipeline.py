def fake_risk_vector(bucket: str) -> dict:
    """
    Generates a mock risk vector to simulate the output of Person 1's pipeline.
    This provides hand-crafted score dictionaries for the four defined risk
    buckets (Low, Moderate, High, Critical) while matching the shared contract shape.
    """
    bucket_lower = bucket.lower()
    
    if bucket_lower == "low":
        return {
            "scores": {
                "acute_distress": 10.0,
                "self_harm_risk": 5.0,
                "fear_of_retaliation": 10.0
            },
            "bucket": "low"
        }
    elif bucket_lower == "moderate":
        return {
            "scores": {
                "acute_distress": 35.0,
                "self_harm_risk": 20.0,
                "fear_of_retaliation": 40.0
            },
            "bucket": "moderate"
        }
    elif bucket_lower == "high":
        return {
            "scores": {
                "acute_distress": 70.0,
                "self_harm_risk": 65.0,
                "fear_of_retaliation": 60.0
            },
            "bucket": "high"
        }
    elif bucket_lower == "critical":
        return {
            "scores": {
                "acute_distress": 95.0,
                "self_harm_risk": 90.0,
                "fear_of_retaliation": 85.0
            },
            "bucket": "critical"
        }
    else:
        raise ValueError(f"Unknown bucket level: {bucket}")

if __name__ == "__main__":
    # Simple test logic
    print("Low:", fake_risk_vector("low"))
    print("Moderate:", fake_risk_vector("moderate"))
    print("High:", fake_risk_vector("high"))
    print("Critical:", fake_risk_vector("critical"))
