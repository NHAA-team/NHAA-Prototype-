from extract_dict import compute_svi, test_text, LIVE_KEYWORDS

# Add the missing robust words to LIVE_KEYWORDS
LIVE_KEYWORDS["acute_distress"].extend(["hidden", "chhipi", "chhupa", "chhipa", "goli mari", "goli chalai"])
LIVE_KEYWORDS["intimidation"].extend(["goli mari"])
LIVE_KEYWORDS["fear_of_retaliation"].extend(["hidden", "chhipi", "chhupa", "chhipa", "goli mari", "goli chalai"])
LIVE_KEYWORDS["social_isolation"].extend(["chhipi", "chhupa", "chhipa"])
LIVE_KEYWORDS["self_harm_risk"].extend(["goli mari"])

en_text = "shoot at the back and feet i am hidden and scared"
en_text_2 = "shot at the back and feet i am hidden and scared"

hi_text_3 = "peeche aur pair par goli mari main chhip kar dari hui hoon"
hi_text_4 = "peeth pe aur pair me goli mari aur main chhupi hui hu dar lag raha hai"

test_text(en_text, "English: shoot")
test_text(en_text_2, "English: shot")
test_text(hi_text_3, "Hindi 3: mari, chhip")
test_text(hi_text_4, "Hindi 4: mari, chhupi")

