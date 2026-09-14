import requests
import wave
import numpy as np

url = "https://huggingface.co/datasets/reach-vb/random-audio/resolve/main/sam_01.wav"
headers = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(url, headers=headers)
with open("real_low_risk_hf.wav", "wb") as f:
    f.write(response.content)
