import ast

def extract_dict(filename, dict_name):
    with open(filename, 'r') as f:
        tree = ast.parse(f.read())
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == dict_name:
                    return ast.literal_eval(node.value)
    return None

LIVE_KEYWORDS = extract_dict("merged_pipeline_server.py", "LIVE_KEYWORDS")

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

en_text = "shoot at the back and feet i am hidden and scared"
hi_text_1 = "peeth par aur pair par goli maar di main chhupi hu aur dari hui hu"
hi_text_2 = "peeth aur pair mein goli lagi hai main chhupi hoon aur dari hui hoon"
hi_text_3 = "peeche aur pair par goli mari main chhip kar dari hui hoon"

test_text(en_text, "English")
test_text(hi_text_1, "Hindi 1")
test_text(hi_text_2, "Hindi 2")
test_text(hi_text_3, "Hindi 3")

