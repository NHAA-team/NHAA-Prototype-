import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "http://www.voiptroubleshooter.com/open_speech/american/OSI_AmEn_01_M.wav"
headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, context=ctx) as response, open("real_low_risk.wav", 'wb') as out_file:
        data = response.read()
        out_file.write(data)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
