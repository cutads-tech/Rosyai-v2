import torch
import torchaudio
import numpy as np
from speechbrain.inference import SpeakerRecognition
from audioio import record_voice

model = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec",
    run_opts={"device": "cuda"}
)

print("🎤 Speak normally for 5 seconds…")

wav_path = record_voice(duration=5)

# Load audio correctly
waveform, sr = torchaudio.load(wav_path)
if sr != 16000:
    waveform = torchaudio.functional.resample(waveform, sr, 16000)

# Encode
emb = model.encode_batch(waveform).squeeze().cpu().numpy()

np.save("auth/owner_voice2.npy", emb)
print("✅ Voice enrolled successfully")
