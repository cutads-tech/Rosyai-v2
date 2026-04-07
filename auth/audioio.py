"""
audioio.py  —  Voice input / output

FIXES:
  1. dynamic_energy_threshold=True disabled — threshold drifts high while Rosy
     speaks, making her deaf to next command. Replaced with manual cap + reset.
  2. sr.RequestError no longer immediately triggers Whisper — retries Google STT
     twice and checks internet before deciding it's truly offline.
  3. Whisper fallback only activates when internet is genuinely unreachable.
  4. Fresh sr.Microphone() on every call (previous bug — stream dies after first use).
"""

import time
import socket

# ── Recording deps ────────────────────────────
try:
    import sounddevice as sd
    import scipy.io.wavfile as wav
    SD_OK = True
except ImportError:
    SD_OK = False

# ── Speech Recognition ────────────────────────
try:
    import speech_recognition as sr
    SR_OK = True
except ImportError:
    SR_OK = False
    print("[audioio] speech_recognition not installed.")

# ── Whisper (optional offline STT) ────────────
# Guard against broken 'whisper' package (TypeError on Windows/Py3.13)
WHISPER_MODEL = None
WHISPER_OK    = False
try:
    import whisper as _whisper_pkg
    WHISPER_OK = True
except Exception as e:
    print(f"[audioio] Whisper disabled ({type(e).__name__}). "
          "Run: pip uninstall whisper -y && pip install openai-whisper")

SAMPLE_RATE = 16000

# Energy threshold limits
_ENERGY_MIN  = 200    # never go below this (too sensitive → picks up noise)
_ENERGY_MAX  = 3500   # FIX: cap so it never drifts high enough to miss speech
_ENERGY_INIT = 300    # start value


# ─────────────────────────────────────────────────────────────
# Shared Recognizer  (safe to reuse — only Microphone is recreated)
# ─────────────────────────────────────────────────────────────
if SR_OK:
    _recognizer = sr.Recognizer()
    _recognizer.energy_threshold         = _ENERGY_INIT
    # FIX: disabled dynamic threshold — it climbs during TTS playback and
    #      makes the mic deaf for the next several seconds
    _recognizer.dynamic_energy_threshold = False
    _recognizer.pause_threshold          = 0.7
    _recognizer.non_speaking_duration    = 0.4
    _recognizer.operation_timeout        = None

    try:
        print("[audioio] Calibrating microphone…")
        with sr.Microphone() as _tmp:
            _recognizer.adjust_for_ambient_noise(_tmp, duration=1.0)
            # Clamp after calibration so it never starts too high
            _recognizer.energy_threshold = max(
                _ENERGY_MIN,
                min(_recognizer.energy_threshold, _ENERGY_MAX)
            )
        print(f"[audioio] Ready  (energy_threshold={_recognizer.energy_threshold:.0f})")
    except Exception as e:
        print(f"[audioio] Calibration warning: {e}")


def _internet_ok(host="8.8.8.8", port=53, timeout=2) -> bool:
    """Quick TCP check — returns True if internet is reachable."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


def _reset_threshold():
    """Reset energy threshold if it has drifted too high (from TTS bleed)."""
    if SR_OK and _recognizer.energy_threshold > _ENERGY_MAX:
        print(f"[audioio] Resetting drifted threshold "
              f"{_recognizer.energy_threshold:.0f} → {_ENERGY_INIT}")
        _recognizer.energy_threshold = _ENERGY_INIT


# ─────────────────────────────────────────────────────────────
# PRIMARY LISTEN
# ─────────────────────────────────────────────────────────────
def _google_listen(timeout: int = 8, phrase_limit: int = 12):
    """
    Record one utterance and transcribe via Google STT.
    Fresh sr.Microphone() every call — shared instance dies after first use.
    """
    if not SR_OK:
        return None

    # FIX: reset drifted threshold before every listen attempt
    _reset_threshold()

    try:
        with sr.Microphone() as source:     # fresh instance every call
            # Brief recalibration — keeps accurate but CLAMPS the result
            _recognizer.adjust_for_ambient_noise(source, duration=0.25)
            _recognizer.energy_threshold = max(
                _ENERGY_MIN,
                min(_recognizer.energy_threshold, _ENERGY_MAX)
            )
            print(f"Listening…  (threshold={_recognizer.energy_threshold:.0f})")
            audio = _recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_limit
            )
    except sr.WaitTimeoutError:
        return None
    except OSError as e:
        print(f"[audioio] Mic error: {e}")
        return None
    except Exception as e:
        print(f"[audioio] Record error: {e}")
        return None

    # Transcription — try Hinglish-friendly en-IN first
    for lang in ("en-IN", "hi-IN"):
        try:
            text = _recognizer.recognize_google(audio, language=lang)
            if text and text.strip():
                return text.strip()
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            # FIX: transient error → don't jump to Whisper yet, check internet
            print(f"[audioio] Google STT error: {e}")
            return None     # caller will retry; Whisper only used in listen()
        except Exception as e:
            print(f"[audioio] Transcription error: {e}")
            return None

    return None


# ─────────────────────────────────────────────────────────────
# WHISPER OFFLINE FALLBACK  (only when internet is truly gone)
# ─────────────────────────────────────────────────────────────
def _whisper_listen(duration: int = 5):
    global WHISPER_MODEL, WHISPER_OK
    if not WHISPER_OK or not SD_OK:
        return None
    try:
        if WHISPER_MODEL is None:
            import whisper as _w
            print("[audioio] Loading Whisper tiny…")
            WHISPER_MODEL = _w.load_model("tiny")
            print("[audioio] Whisper loaded ✓")

        print(f"Recording {duration}s offline…")
        data = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE, channels=1, dtype="float32"
        )
        sd.wait()
        result = WHISPER_MODEL.transcribe(data.flatten(), language="en", fp16=False)
        text = result.get("text", "").strip()
        return text if text else None
    except Exception as e:
        print(f"[audioio] Whisper error: {e}")
        WHISPER_OK = False
        return None


# ─────────────────────────────────────────────────────────────
# PUBLIC listen()
# ─────────────────────────────────────────────────────────────
_google_fail_streak = 0           # consecutive Google STT failures
_GOOGLE_MAX_STREAK  = 3           # how many failures before checking internet

def listen(timeout: int = 8) -> str | None:
    """
    Listen for one voice command. Returns text or None (caller loops).
    
    FIX: Only falls back to Whisper after 3 consecutive Google failures AND
         internet is confirmed unreachable. Prevents false offline fallback.
    """
    global _google_fail_streak

    result = _google_listen(timeout=timeout)

    if result:
        _google_fail_streak = 0     # reset on success
        print(f"[You] {result}")
        return result

    # Google returned None (timeout or error)
    _google_fail_streak += 1

    # FIX: only try Whisper after repeated failures + confirmed no internet
    if WHISPER_OK and _google_fail_streak >= _GOOGLE_MAX_STREAK:
        if not _internet_ok():
            print("[audioio] Internet unreachable — switching to Whisper offline.")
            _google_fail_streak = 0
            result = _whisper_listen()
            if result:
                print(f"[You/offline] {result}")
                return result
        else:
            # Internet is fine — Google just had a hiccup, reset streak
            _google_fail_streak = 0

    return None


# ─────────────────────────────────────────────────────────────
# RAW RECORDER  (auth / enrolment)
# ─────────────────────────────────────────────────────────────
def record_voice(duration: int = 3, filename: str = "temp_voice.wav") -> str:
    if not SD_OK:
        return filename
    print(f"Recording {duration}s…")
    data = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                  channels=1, dtype="float32")
    sd.wait()
    wav.write(filename, SAMPLE_RATE, data)
    return filename


# ─────────────────────────────────────────────────────────────
# OFFLINE TTS fallback  (pyttsx3)
# ─────────────────────────────────────────────────────────────
_tts_engine = None
PYTTSX3_OK  = False
try:
    import pyttsx3
    _tts_engine = pyttsx3.init()
    for _v in _tts_engine.getProperty("voices"):
        if any(k in _v.name.lower() for k in ("female","zira","hazel","susan","heera")):
            _tts_engine.setProperty("voice", _v.id)
            break
    _tts_engine.setProperty("rate", 165)
    PYTTSX3_OK = True
except Exception:
    pass

def speak(text: str):
    if PYTTSX3_OK and _tts_engine:
        _tts_engine.say(text); _tts_engine.runAndWait()
    else:
        print(f"[SPEAK] {text}")
