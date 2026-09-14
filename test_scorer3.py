from extract_dict import compute_svi, test_text

LIVE_KEYWORDS = {
    "acute_distress": [
        "help", "scared", "hide", "hiding", "run", "running",
        "shot", "shoot", "gun", "gunshot", "bleeding very much", "bleeding heavily",
        "bachao", "madad", "dar", "bhago", "chhup", "chhip", "chhupe",
        "goli lagi", "goli maar", "bandook", "bahut khoon beh raha", "bahut khoon",
        "maar", "peeche"
    ],
    "depression": [
        "hopeless", "sad", "bleeding", "blood",
        "udaas", "dukhi", "khoon", "khoon beh", "zakhm", "zakhmi", "chot", "chot lagi", "dard"
    ],
    "self_harm_risk": [
        "kill", "suicide", "die", "bleed",
        "marna", "khoon beh", "goli lagi", "bahut khoon"
    ],
    "fear_of_retaliation": [
        "follow", "following", "scared of him",
        "shot", "shoot", "gun", "gunshot",
        "dhamki", "peecha", "peeche aa rahe", "ped ke peeche",
        "goli lagi", "goli maar", "bandook"
    ],
    "intimidation": [
        "weapon", "gun", "knife", "hit", "beat", "shot", "shoot",
        "hathiyar", "bandook", "maara", "goli", "goli maar", "khoon", "khoon beh", "bahut khoon"
    ],
    "dissociation": [
        "blank", "numb",
        "sab blank", "behosh"
    ],
    "social_isolation": [
        "alone", "no one",
        "akela", "ped ke peeche", "jungle mein"
    ]
}

def compute_svi(scores: dict) -> dict:
    weights = {
        "self_harm_risk": 0.22, "fear_of_retaliation": 0.18, "acute_distress": 0.16,
        "intimidation": 0.14, "dissociation": 0.10, "depression": 0.08,
        "chronic_trauma_indicators": 0.07, "social_isolation": 0.05,
    }
    weighted_sum = sum(scores.get(k, 0.0) * w * 100 for k, w in weights.items())
    active_dims = sum(1 for k in weights if scores.get(k, 0.0) > 0)
    breadth_mult = 1.0 + (active_dims / 8.0) * 0.95
    raw = weighted_sum * breadth_mult
    raw = min(100.0, max(0.0, raw))
    bucket = "low" if raw <= 25 else "moderate" if raw <= 50 else "high" if raw <= 75 else "critical"
    return {"value": round(raw, 2), "bucket": bucket}

def test_text(text, label):
    scores = {}
    matched = {}
    for dim, kw_list in LIVE_KEYWORDS.items():
        matches = [kw for kw in kw_list if kw in text.lower()]
        if matches:
            matched[dim] = matches
            scores[dim] = 0.8
    print(f"\n--- {label} ---")
    print("Text:", text)
    print("Matches:", matched)
    svi = compute_svi(scores)
    print("SVI:", svi)

en_text = "shot on leg by someone bleeding very much"
hi_text_3 = "pair par goli lagi bahut khoon nikal raha hai"

test_text(en_text, "English: shot on leg by someone bleeding very much")
test_text(hi_text_3, "Hindi: pair par goli lagi bahut khoon nikal raha hai")

