import pvporcupine
import pyaudio
import struct
import os
from dotenv import load_dotenv

load_dotenv()

def wait_for_wake_word():
    porcupine = pvporcupine.create(
        access_key=os.getenv("PORCUPINE_ACCESS_KEY"),
        keyword_paths=["Heyrosy.ppn"]
    )

    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print("🌹 Waiting for 'Hey Rosy'...")

    try:
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from(
                "h" * porcupine.frame_length, pcm
            )

            if porcupine.process(pcm) >= 0:
                print("✨ Wake word detected")
                return   # 🔥 DO NOT EXIT
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()