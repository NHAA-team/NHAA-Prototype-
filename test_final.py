import ast, json

def extract_live_keywords(filename):
    with open(filename, 'r') as f:
        source = f.read()
    # Find LIVE_KEYWORDS dict by scanning for the assignment
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'LIVE_KEYWORDS':
                    return ast.literal_eval(node.value)
    return None

LIVE_KEYWORDS = extract_live_keywords("merged_pipeline_server.py")
if not LIVE_KEYWORDS:
    print("ERROR: Could not extract LIVE_KEYWORDS")
    exit(1)

def compute_svi(scores):
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

def test(text, label):
    scores = {}
    matched = {}
    for dim, kw_list in LIVE_KEYWORDS.items():
        matches = [kw for kw in kw_list if kw in text.lower()]
        if matches:
            matched[dim] = matches
            scores[dim] = 0.8
    svi = compute_svi(scores)
    dims = len(matched)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  Text: {text}")
    print(f"  Dims hit: {dims}  |  SVI: {svi['value']}%  |  Bucket: {svi['bucket'].upper()}")
    for d, m in matched.items():
        print(f"    {d}: {m}")

print("\n" + "="*60)
print("  SCENARIO: Shot at back and feet, hidden and scared")
print("="*60)

test("shoot at the back and feet i am hidden and scared", 
     "ENGLISH")

test("peeth par aur pair par goli maar di main chhupi hu aur dari hui hu",
     "HINDI v1: goli maar di, chhupi, dari hui")

test("peeth aur pair mein goli lagi hai main chhupi hoon aur dari hui hoon",
     "HINDI v2: goli lagi, chhupi, dari hui")

test("peeche aur pair par goli mari main chhip kar dari hui hoon",
     "HINDI v3: goli mari, chhip, dari hui")

test("peeth pe aur pair me goli mari aur main chhupi hui hu dar lag raha hai",
     "HINDI v4: goli mari, chhupi, dar lag raha")

print("\n" + "="*60)
print("  SCENARIO: Someone following, shot leg, bleeding, hiding")
print("="*60)

test("someone following me and shot on my leg bleeding very much i am hiding beside a tree",
     "ENGLISH")

test("usne mere pair par goli maar di mera bahut khoon beh raha hai main ek ped ke peeche chhupi hu koi mera peecha kar raha hai",
     "HINDI")

print("\n" + "="*60)
print("  SCENARIO: Lost purse (should be LOW)")
print("="*60)

test("i lost my purse somewhere i think i dropped it at the market",
     "ENGLISH")

test("mera purse kho gaya hai lagta hai market mein gir gaya",
     "HINDI")

