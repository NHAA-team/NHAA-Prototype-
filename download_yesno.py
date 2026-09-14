import subprocess
import sys

try:
    import torchaudio
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "torchaudio"])
    import torchaudio

dataset = torchaudio.datasets.YESNO("./", download=True)
waveform, sample_rate, labels = dataset[0]
torchaudio.save('yesno_sample.wav', waveform, sample_rate)
print("Saved yesno_sample.wav")
