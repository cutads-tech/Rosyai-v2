import pyttsx3
import threading
import queue
import re

engine = pyttsx3.init()
engine.setProperty("voice", engine.getProperty("voices")[1].id)

speech_queue = queue.Queue()
STOP_FLAG = False

def _tts_worker():
    global STOP_FLAG
    while True:
        text, rate = speech_queue.get()
        if STOP_FLAG:
            engine.stop()
            speech_queue.queue.clear()
            STOP_FLAG = False
            speech_queue.task_done()
            continue

        engine.setProperty("rate", rate)
        engine.say(text)
        engine.runAndWait()
        speech_queue.task_done()

threading.Thread(target=_tts_worker, daemon=True).start()

def stop_speaking():
    global STOP_FLAG
    STOP_FLAG = True
    engine.stop()
    with speech_queue.mutex:
        speech_queue.queue.clear()
def speak_streaming(text, emotion="caring"):
    if not text:
        return

    if emotion == "happy":
        rate = 175
    elif emotion == "angry":
        rate = 190
    else:
        rate = 155

    sentences = re.split(r'(?<=[.!?]) +', text)
    for s in sentences:
        if s.strip():
            speech_queue.put((s.strip(), rate))


voices = engine.getProperty("voices")
for v in voices:
    if "female" in v.name.lower() or "zira" in v.name.lower():
        engine.setProperty("voice", v.id)
        break

engine.setProperty("rate", 165)

def speak(text: str, emotion: str = "caring"):
    """
    Offline fallback TTS (basic, non-streaming)
    """
    engine.say(text)
    engine.runAndWait()