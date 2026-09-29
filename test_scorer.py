import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "person1"))
sys.path.append(os.path.join(BASE_DIR, "person2"))

# Just define the LIVE_KEYWORDS that matter to us here for a quick check
LIVE_KEYWORDS = {
    "acute_distress": [
        "help", "scared", "hide", "hiding", "run", "running",
        "bachao", "madad", "dar", "bhago", "chhup", "chhip", "chhupe", "maar", "shot", "peeche"
    ],
    "depression": [
        "hopeless", "sad", "bleeding", "blood",
        "udaas", "dukhi", "khoon", "khoon beh", "zakhm", "zakhmi", "chot", "chot lagi", "dard"
    ],
    "self_harm_risk": [
        "kill", "suicide", "die", "bleed",
        "marna", "khoon beh", "goli lagi"
    ],
    "fear_of_retaliation": [
        "follow", "following", "scared of him",
        "dhamki", "peecha", "peeche aa rahe", "ped ke peeche"
    ],
    "intimidation": [
        "weapon", "gun", "knife", "hit", "beat",
        "hathiyar", "bandook", "maara", "goli", "goli maar", "khoon", "khoon beh"
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


en_text = "someone following me and shot on leg by someone bleeding very much and i am hiding beside a tree"
hi_text = "usne mere pair par goli maar di mera bahut khoon beh raha hai main ek ped ke peeche chhupi hu koi mera peecha kar raha hai"

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

test_text(en_text, "English")
test_text(hi_text, "Hindi")
