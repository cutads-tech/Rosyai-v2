import time

try:
    from tts.sarvamai_tts2 import speak_async
except Exception:
    try:
        from tts.emotional_tts import speak_streaming as speak_async
    except Exception:
        def speak_async(text, emotion="caring"):
            print(f"[TTS] {text}")

try:
    from web_control2 import search_youtube, search_google, scroll_down, scroll_up
except Exception as e:
    print(f"[task_executor] web_control2 import error: {e}")


def execute_task_chain(steps):
    """Execute a list of (action, data) tuples in sequence."""
    for action, data in steps:
        try:
            if action == "open_youtube":
                speak_async("YouTube khol rahi hoon", "happy")
                search_youtube("")
                time.sleep(2)

            elif action == "search_youtube":
                speak_async(f"{data} search kar rahi hoon", "happy")
                search_youtube(data or "")
                time.sleep(2)

            elif action == "search_google":
                speak_async(f"{data} dhoondh rahi hoon", "caring")
                search_google(data or "")

            elif action == "scroll_down":
                scroll_down()

            elif action == "scroll_up":
                scroll_up()

            elif action == "speak":
                speak_async(str(data), "happy")

            elif action == "wait":
                secs = float(data) if data else 1.0
                time.sleep(secs)

        except Exception as e:
            print(f"[task_executor] Step '{action}' error: {e}")
