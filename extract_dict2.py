from extract_dict import test_text

en_text = "shot on leg by someone bleeding very much"
hi_text = "kisi ne pair par goli maar di aur bahut khoon beh raha hai"
hi_text_2 = "kisi ne goli maar di bahut khoon beh raha hai"
hi_text_3 = "pair par goli lagi bahut khoon nikal raha hai"

test_text(en_text, "English: shot on leg by someone bleeding very much")
test_text(hi_text, "Hindi 1")
test_text(hi_text_2, "Hindi 2")
test_text(hi_text_3, "Hindi 3")

