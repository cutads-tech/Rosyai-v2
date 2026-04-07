import threading
import time

try:
    from screen_vision import describe_screen
    SCREEN_OK = True
except ImportError:
    SCREEN_OK = False

try:
    from vision_yolo import detect_objects
    YOLO_OK = True
except ImportError:
    YOLO_OK = False

LATEST_STATE: dict = {}
_PREV_TEXT: str = ""
_RUNNING: bool = False
_PAUSED: bool = False
_INTERVAL: float = 1.5      # seconds between scans (reduce for faster, increase to save CPU)
_lock = threading.Lock()

_change_callbacks: list = []   # functions called when screen changes significantly


def add_change_callback(fn):
    """Register a function to be called when screen content changes."""
    _change_callbacks.append(fn)


def _notify_change(state: dict):
    for fn in _change_callbacks:
        try:
            fn(state)
        except Exception:
            pass


def _vision_worker():
    global LATEST_STATE, _PREV_TEXT, _RUNNING, _PAUSED

    while _RUNNING:
        if _PAUSED:
            time.sleep(0.5)
            continue

        try:
            new_state: dict = {}

            if SCREEN_OK:
                screen = describe_screen()
                new_state = {
                    "text":        screen.get("visible_text", "")[:400],
                    "windows":     screen.get("windows_detected", 0),
                    "objects":     screen.get("objects_detected", 0),
                    "top_objects": screen.get("top_objects", []),
                    "ts":          time.time(),
                }

            if YOLO_OK:
                objs = detect_objects()
                new_state["detected_items"] = [o["name"] for o in objs[:10]]

            with _lock:
                # Detect meaningful text change
                new_text = new_state.get("text", "")
                if new_text and new_text != _PREV_TEXT:
                    new_state["changed"] = True
                    _notify_change(new_state)
                    _PREV_TEXT = new_text

                new_state["changed"] = new_state.get("changed", False)
                LATEST_STATE = new_state

        except Exception as e:
            with _lock:
                LATEST_STATE = {"error": str(e), "ts": time.time()}

        time.sleep(_INTERVAL)


def start_vision(interval: float = 1.5):
    """Start the background vision loop."""
    global _RUNNING, _PAUSED, _INTERVAL
    _INTERVAL = interval
    _RUNNING = True
    _PAUSED = False
    t = threading.Thread(target=_vision_worker, daemon=True, name="VisionLoop")
    t.start()
    print(f"[vision_loop] Started (interval={interval}s) ✓")


def stop_vision():
    global _RUNNING
    _RUNNING = False
    print("[vision_loop] Stopped.")


def pause_vision():
    global _PAUSED
    _PAUSED = True


def resume_vision():
    global _PAUSED
    _PAUSED = False


def get_state() -> dict:
    with _lock:
        return dict(LATEST_STATE)


def get_text() -> str:
    return get_state().get("text", "")


def is_running() -> bool:
    return _RUNNING and not _PAUSED
