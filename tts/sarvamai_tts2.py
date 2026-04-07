import os
import re
import io
import time
import base64
import queue
import threading
import numpy as np
import requests
import sounddevice as sd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("SARVAM_API_KEY", "")
TTS_URL = "https://api.sarvam.ai/text-to-speech"

# ── Emotion → TTS pace mapping ─────────────────
# Sarvam pace range: 0.5 (slow) to 2.0 (fast), natural = 1.0
EMOTION_PACE = {
    "happy":    1.05,   # slightly upbeat
    "excited":  1.10,
    "caring":   0.95,   # warm, relaxed — main personality voice
    "sad":      0.85,   # slower, softer
    "thinking": 0.90,   # measured, deliberate
    "angry":    1.05,
    "default":  0.95,   # ✅ FIX: default slightly slower = more natural
}

# ── Playback control ────────────────────────────
_speech_queue: queue.Queue = queue.Queue()
_STOP = False


# ══════════════════════════════════════════════════
# TEXT CLEANER  — makes text sound natural when spoken
# ══════════════════════════════════════════════════
def _clean_for_speech(text: str) -> str:
    """Strip markdown and symbols that sound terrible in TTS."""
    # Remove markdown bold/italic
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,2}(.+?)_{1,2}', r'\1', text)

    # Remove code blocks and inline code
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)

    # Remove markdown headings
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Convert bullet points to natural pauses
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+[.)]\s+', '', text, flags=re.MULTILINE)

    # Remove URLs
    text = re.sub(r'https?://\S+', 'the link', text)

    # Remove emojis (they break TTS or get read as "fire emoji")
    text = re.sub(
        r'[\U0001F300-\U0001FFFF\U00002600-\U000027BF\U0000FE00-\U0000FEFF]',
        '', text
    )

    # Expand common abbreviations for natural reading
    text = re.sub(r'\bvs\b', 'versus', text, flags=re.I)
    text = re.sub(r'\betc\b\.?', 'etcetera', text, flags=re.I)
    text = re.sub(r'\be\.g\b\.?', 'for example', text, flags=re.I)
    text = re.sub(r'\bi\.e\b\.?', 'that is', text, flags=re.I)
    text = re.sub(r'\bw/\b', 'with', text)
    text = re.sub(r'\bw/o\b', 'without', text)

    # Remove parenthetical asides that interrupt speech flow
    text = re.sub(r'\([^)]{0,60}\)', '', text)

    # Clean up extra whitespace and blank lines
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.strip()

    return text


# ══════════════════════════════════════════════════
# SMART SENTENCE CHUNKER
# — splits at natural speech boundaries, not char count
# ══════════════════════════════════════════════════
_MAX_CHUNK = 450   # Sarvam's safe limit

def _split_sentences(text: str) -> list[str]:
    """Split on sentence-ending punctuation for natural rhythm."""
    # Split on . ! ? ; — keeping the delimiter
    raw = re.split(r'(?<=[.!?;])\s+', text.strip())
    chunks = []
    current = ""

    for sentence in raw:
        if not sentence.strip():
            continue
        # If adding this sentence would exceed limit, flush first
        if current and len(current) + 1 + len(sentence) > _MAX_CHUNK:
            chunks.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip() if current else sentence
    if current.strip():
        chunks.append(current.strip())

    # Safety: if any single sentence is still too long, hard-split it
    final = []
    for chunk in chunks:
        if len(chunk) <= _MAX_CHUNK:
            final.append(chunk)
        else:
            # Split at comma or dash as secondary boundary
            sub = re.split(r'(?<=[,—])\s+', chunk)
            buf = ""
            for s in sub:
                if buf and len(buf) + 1 + len(s) > _MAX_CHUNK:
                    final.append(buf.strip())
                    buf = s
                else:
                    buf = (buf + " " + s).strip() if buf else s
            if buf:
                final.append(buf.strip())

    return [c for c in final if c]


# ══════════════════════════════════════════════════
# SARVAM API CALL
# ══════════════════════════════════════════════════
def _synthesize(text_chunk: str, pace: float = 1.0):
    """
    Call Sarvam TTS API. Returns (audio_numpy, sample_rate) or (None, None).
    """
    if not API_KEY:
        return None, None

    headers = {
        "api-subscription-key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "inputs":              [text_chunk],
        "target_language_code":"en-IN",      # ✅ FIX: en-IN gives natural Hinglish rhythm
        "speaker":             "shreya",      # ✅ FIX: meera is warmer/more human (was "shreya")
        "model":               "bulbul:v3",
        "pace":                round(pace, 2),
        "speech_sample_rate":  24000,        # ✅ FIX: higher rate = crisper, less robotic
        "enable_preprocessing":True,        
        "output_audio_codec":  "wav",
    }

    try:
        r = requests.post(TTS_URL, headers=headers, json=payload, timeout=15)
    except Exception as e:
        print(f"[TTS] Network error: {e}")
        return None, None

    if r.status_code != 200:
        try:    print(f"[TTS] API error {r.status_code}:", r.json())
        except: print(f"[TTS] API error {r.status_code}:", r.text[:200])
        return None, None

    # Parse response — Sarvam returns JSON with base64 audio list or raw WAV
    ct = r.headers.get("Content-Type", "")
    try:
        if "application/json" in ct:
            j = r.json()
            b64 = (j.get("audios") or [None])[0] or j.get("audio")
            if not b64:
                print("[TTS] Unexpected JSON:", j)
                return None, None
            wav_bytes = base64.b64decode(b64)
        else:
            wav_bytes = r.content

        import soundfile as sf
        arr, sr = sf.read(io.BytesIO(wav_bytes))
        arr = arr.astype(np.float32)
        return arr, sr

    except Exception:
        # scipy fallback
        try:
            from scipy.io.wavfile import read as wavread
            sr, arr = wavread(io.BytesIO(wav_bytes if 'wav_bytes' in dir() else r.content))
            arr = arr.astype(np.float32)
            if arr.max() > 1.0:
                arr /= 32768.0
            return arr, sr
        except Exception as e:
            print(f"[TTS] Audio decode error: {e}")
            return None, None


# ══════════════════════════════════════════════════
# BACKGROUND PLAYBACK THREAD  (single thread, queued)
# ══════════════════════════════════════════════════
def _playback_worker():
    """Single background thread that drains the speech queue."""
    global _STOP
    while True:
        item = _speech_queue.get()
        if item is None:            # sentinel — thread shutdown
            break
        chunks, pace = item
        _STOP = False

        for i, chunk in enumerate(chunks):
            if _STOP:
                break
            if not chunk.strip():
                continue

            wav_arr, sr = _synthesize(chunk, pace)
            if wav_arr is None:
                # TTS failed for this chunk — fall back to pyttsx3
                try:
                    import pyttsx3
                    _e = pyttsx3.init()
                    _e.say(chunk)
                    _e.runAndWait()
                    del _e
                except Exception:
                    print(f"[TTS fallback] {chunk}")
                continue

            sd.play(wav_arr, sr)
            sd.wait()

            # FIX: inter-sentence pause — only between actual sentence ends
            # Short pause after . or ? or !, tiny gap after comma/semicolon
            if i < len(chunks) - 1:
                last_char = chunk.rstrip()[-1] if chunk.rstrip() else ""
                if last_char in ".?!":
                    time.sleep(0.08)     # natural breath between sentences
                elif last_char in ",;":
                    time.sleep(0.03)     # tiny clause pause
                # no sleep for mid-sentence splits

        _speech_queue.task_done()


_worker_thread = threading.Thread(target=_playback_worker, daemon=True, name="TTS")
_worker_thread.start()


# ══════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════
def speak_async(text: str, emotion: str = "caring"):
    """
    Queue text for speech. Returns immediately (non-blocking).
    Cleans markdown, splits at sentence boundaries, uses emotion-mapped pace.
    """
    if not text or not text.strip():
        return

    clean  = _clean_for_speech(text)
    if not clean:
        return

    pace   = EMOTION_PACE.get(emotion, EMOTION_PACE["default"])
    chunks = _split_sentences(clean)

    _speech_queue.put((chunks, pace))


def speak_streaming(text: str, emotion: str = "caring"):
    """Alias — same as speak_async (kept for backward compatibility)."""
    speak_async(text, emotion)


def stop_speaking():
    global _STOP
    _STOP = True
    try:
        sd.stop()
    except Exception:
        pass
    # Drain the queue
    while not _speech_queue.empty():
        try:
            _speech_queue.get_nowait()
            _speech_queue.task_done()
        except Exception:
            break
