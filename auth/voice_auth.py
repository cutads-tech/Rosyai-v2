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
def verify_voice():
    wav_path = record_voice(duration=3)

    waveform, sr = torchaudio.load(wav_path)
    if sr != 16000:
        waveform = torchaudio.functional.resample(waveform, sr, 16000)

    test_emb = model.encode_batch(waveform).squeeze().cpu().numpy()
    owner_emb = np.load("auth/owner_voice.npy")

    score = np.dot(test_emb, owner_emb) / (
        np.linalg.norm(test_emb) * np.linalg.norm(owner_emb)
    )

    print("🔐 Voice similarity score:", round(float(score), 3))
    return score > 0.7

if __name__ == "__main__":
    print("🎧 Testing voice authentication…")
    print("Verified:", verify_voice())
