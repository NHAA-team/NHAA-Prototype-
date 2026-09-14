import sys
import subprocess

try:
    from datasets import load_dataset
    import soundfile as sf
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets", "soundfile"])
    from datasets import load_dataset
    import soundfile as sf

print("Loading MINDS-14 dataset...")
ds = load_dataset("PolyAI/minds14", "en-US", split="train")
sample = ds[0]

audio_array = sample["audio"]["array"]
sample_rate = sample["audio"]["sampling_rate"]

# The pipeline wants 16kHz. If it's not 16kHz we might need to resample, but we can write it to wav and let ffmpeg do it.
sf.write("minds14_sample.wav", audio_array, sample_rate)
print("Saved to minds14_sample.wav")
