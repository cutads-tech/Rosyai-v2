import os
import sys
import time
import json
import random
import datetime
import threading
import traceback
import urllib.parse
import webbrowser
import re
from whatsapp_command_handler import WhatsAppCommandHandler
import dotenv
dotenv.load_dotenv()
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# ══════════════════════════════════════════════
# SAFE IMPORTS WITH FALLBACKS
# ══════════════════════════════════════════════
def _safe_import(module_path, alias=None, fallback=None):
    """Import with graceful fallback."""
    try:
        parts = module_path.split(".")
        if len(parts) == 1:
            mod = __import__(module_path)
        else:
            mod = __import__(module_path, fromlist=[parts[-1]])
        return mod
    except Exception as e:
        print(f"[ROSY] Warning: Could not import '{module_path}': {e}")
        return fallback


# ── TTS ──────────────────────────────────────
try:
    from tts.sarvamai_tts2 import speak_async, stop_speaking
except Exception:
    try:
        from tts.emotional_tts import speak_streaming as _speak_sync
        import threading as _t
        def speak_async(text, emotion="caring"):
            _t.Thread(target=_speak_sync, args=(text, emotion), daemon=True).start()
        def stop_speaking(): pass
    except Exception:
        def speak_async(text, emotion="caring"):
            print(f"[ROSY speaks] {text}")
        def stop_speaking(): pass
    print("[ROSY] Using fallback TTS.")

# ── LLM ──────────────────────────────────────
try:
    from llm_mistral import generate_stream
    MISTRAL_AVAILABLE = True
except Exception as e:
    print(f"[ROSY] Mistral not available: {e}")
    MISTRAL_AVAILABLE = False
    def generate_stream(prompt, history):
        yield "[Mistral not loaded]"

# ── External LLM ─────────────────────────────
try:
    from external_llm import ask_gemini, ask_perplexity, ask_gpt
except Exception:
    def ask_gemini(q): return "[Gemini unavailable]"
    def ask_perplexity(q): return "[Perplexity unavailable]"
    def ask_gpt(q): return "[GPT unavailable]"

# ── Memory ────────────────────────────────────
from memory import Memory
# ✅ BUG FIX #4: Only import from memory_system (avoid double import conflict)
from memory_system import remember, recall, forget, list_memories

# ── Audio ─────────────────────────────────────
try:
    from audioio import listen
except Exception:
    def listen(timeout=5): return input("You: ").strip() or None

# ── Agent Brain ───────────────────────────────
try:
    from agent_brain import observe, think, plan, act, self_correct, improve_code
except Exception as e:
    print(f"[ROSY] agent_brain warning: {e}")

# ── Screen Vision ─────────────────────────────
try:
    from screen_vision import (
        read_screen_text, smart_click, detect_gui_elements,
        detect_windows, describe_screen
    )
    SCREEN_VISION_OK = True
except Exception:
    SCREEN_VISION_OK = False

# ── Vision Loop ───────────────────────────────
try:
    from vision_loop import start_vision, stop_vision, get_state
    VISION_LOOP_OK = True
except Exception:
    VISION_LOOP_OK = False
    def start_vision(): pass
    def stop_vision(): pass
    def get_state(): return {}

# ── PC Control ────────────────────────────────
from pc_control import handle_command, get_system_stats, volume_up, volume_down, mute_volume

# ── Web Control ──────────────────────────────
# ✅ BUG FIX #5: Only import search_youtube from ONE source (web_control2)
try:
    from web_control2 import (
        search_youtube, search_google, scroll_down, scroll_up,
        write_text, start_browser, open_website, google_search, click_link
    )
    WEB_OK = True
except Exception as e:
    print(f"[ROSY] web_control2 warning: {e}")
    WEB_OK = False

try:
    from web_control import play_first_youtube, youtube_play_pause, youtube_next
except Exception:
    def play_first_youtube(): pass
    def youtube_play_pause(): pass
    def youtube_next(): pass

# ── Music ─────────────────────────────────────
try:
    from music_agent import play_song, play_latest_songs, next_video, search_song, play_mood_songs, play_artist, play_by_language, get_play_history, pause_play, prev_video
    MUSIC_OK = True
except Exception:
    MUSIC_OK = False

# ── Automation ────────────────────────────────
try:
    from control import automation as auto
    from control.automation import click, type_text
    AUTO_OK = True
except Exception:
    AUTO_OK = False

# ── Object Detection ─────────────────────────
try:
    from vision_yolo import detect_objects
    YOLO_OK = True
except Exception:
    YOLO_OK = False
    def detect_objects(): return []

# ── File Agent ───────────────────────────────
try:
    from file_agent import list_files, read_file, create_folder, write_file, delete_file, search_files, file_info, open_file, zip_folder, unzip_file
except Exception:
    def list_files(p="."): return os.listdir(p)
    def read_file(p): return open(p).read() if os.path.exists(p) else "File not found"
    def create_folder(p): os.makedirs(p, exist_ok=True); return "Created"
    def write_file(p, c): open(p, "w").write(c); return "Written"
    def delete_file(p): os.remove(p); return "Deleted"

# ── Task Planning ────────────────────────────
try:
    from task_planner import plan_task
    from task_executor import execute_task_chain
except Exception as e:
    print(f"[ROSY] task planner warning: {e}")
    def plan_task(t): return []
    def execute_task_chain(s): pass

# ── Ultra Vision ─────────────────────────────
try:
    from ultra_vision import find_target
except Exception:
    def find_target(t): return None

# ── Smart Command Parser ─────────────────────
try:
    from command_parser import handle_smart_write, parse_write_intent
    SMART_WRITE_OK = True
    print("[ROSY] Smart command parser loaded ✓")
except Exception as _cp_err:
    print(f"[ROSY] command_parser warning: {_cp_err}")
    SMART_WRITE_OK = False
    def handle_smart_write(t): return None
    def parse_write_intent(t): return None

# ── Code Executor ────────────────────────────
try:
    from code_executer import run_python
except Exception:
    def run_python(code): return "code_executer not available"

# ── Wake Word ────────────────────────────────
try:
    from wake_word import wait_for_wake_word
    WAKE_WORD_OK = True
except Exception:
    print("[ROSY] Wake word engine not available. Press Enter to activate.")
    WAKE_WORD_OK = False
    def wait_for_wake_word():
        input("\n[Press Enter to activate ROSY] > ")

# ── Vision Loop ──────────────────────────────
if VISION_LOOP_OK:
    try:
        start_vision()
        print("[ROSY] Vision loop started ✓")
    except Exception as e:
        print(f"[ROSY] Vision loop error: {e}")

# ══════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════
memory = Memory(max_turns=12)
SESSION_START = datetime.datetime.now()
COMMAND_COUNT = 0

def _naturalise(text: str) -> str:
    """
    Post-process LLM reply before it reaches TTS.
    Removes markdown, strips robotic openers, trims length.
    """
    import re as _re

    # Remove markdown formatting
    text = _re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    text = _re.sub(r'_{1,2}(.+?)_{1,2}', r'\1', text)
    text = _re.sub(r'```[\s\S]*?```', '', text)
    text = _re.sub(r'`[^`]+`', '', text)
    text = _re.sub(r'^#{1,6}\s+', '', text, flags=_re.MULTILINE)

    # Convert bullet lists to flowing sentences
    text = _re.sub(r'^\s*[-*•]\s+', '', text, flags=_re.MULTILINE)
    text = _re.sub(r'^\s*\d+[.)]\s+', '', text, flags=_re.MULTILINE)

    # Remove robotic filler openers
    ROBOTIC_OPENERS = (
        r"^(certainly[!,.]?\s*)",
        r"^(of course[!,.]?\s*)",
        r"^(sure[!,.]?\s*)",
        r"^(great question[!,.]?\s*)",
        r"^(absolutely[!,.]?\s*)",
        r"^(i'd be happy to\s*)",
        r"^(i would be happy to\s*)",
        r"^(as an ai(?: language model)?[,.]?\s*)",
        r"^(i am an ai[,.]?\s*)",
    )
    for pat in ROBOTIC_OPENERS:
        text = _re.sub(pat, '', text, flags=_re.IGNORECASE)

    # Collapse multiple newlines to a single space
    text = _re.sub(r'\n{2,}', ' ', text)
    text = _re.sub(r'\n', ' ', text)
    text = _re.sub(r'\s{2,}', ' ', text)

    # Trim if extremely long (TTS should speak short responses)
    words = text.split()
    if len(words) > 120:
        # Cut at last sentence end before word 120
        cut = ' '.join(words[:120])
        last = max(cut.rfind('.'), cut.rfind('!'), cut.rfind('?'))
        text = cut[:last+1] if last > 60 else cut + '...'

    return text.strip()
ROSY_FILLERS = [
    "Processing…", "One moment…", "Right away…",
    "On it…", "Computing…", "Scanning…"
]

ROSY_GREETINGS = {
    "morning": [
        "Good morning. All systems nominal. How can I assist you today?",
        "Morning. Ready when you are.",
    ],
    "afternoon": [
        "Good afternoon. How can I help?",
        "Afternoon. What do you need?",
    ],
    "evening": [
        "Good evening. What can I do for you?",
        "Evening. All systems ready.",
    ],
    "night": [
        "Working late? What do you need?",
        "Good night. Still here if you need me.",
    ],
}

def _get_greeting() -> str:
    h = datetime.datetime.now().hour
    if 5 <= h < 12:    key = "morning"
    elif 12 <= h < 17: key = "afternoon"
    elif 17 <= h < 21: key = "evening"
    else:              key = "night"
    return random.choice(ROSY_GREETINGS[key])


def humanize(text: str) -> str:
    """Add a subtle natural filler for longer responses."""
    if len(text) > 80:
        return f"{random.choice(ROSY_FILLERS)} {text}"
    return text


def detect_tone(text: str) -> str:
    """Detect appropriate TTS tone from reply content."""
    tl = text.lower()
    if any(w in tl for w in ["error", "sorry", "nahi", "couldn't", "fail"]):
        return "sad"
    if any(w in tl for w in ["!", "great", "done", "complete", "🎉", "✅"]):
        return "happy"
    if any(w in tl for w in ["wait", "moment", "processing", "scanning"]):
        return "thinking"
    return "caring"
# =========================
# WHATSAPP COMMAND HANDLING
# =========================
# ══════════════════════════════════════════════
# INTENT CLASSIFIER
# ══════════════════════════════════════════════
def classify_intent(text: str) -> str:
    """Return intent category string for smarter routing."""
    t = text.lower()

    # Specific patterns first
    if any(w in t for w in ["whatsapp", "message to", "send to", "reply to", "read whatsapp"]):
        return "whatsapp"
    if any(w in t for w in ["play song", "play music", "latest song", "next song", "next video", "search song"]):
        return "music"
    if any(w in t for w in ["open ", "close ", "start ", "launch ", "shutdown", "restart", "lock pc"]):
        return "pc_control"
    if any(w in t for w in ["volume", "mute", "brightness"]):
        return "pc_control"
    if any(w in t for w in ["scroll", "click on", "find and click", "what do you see", "read screen", "detect"]):
        return "screen"
    if any(w in t for w in ["youtube", "google", "open website", "browser"]):
        return "web"
    if any(w in t for w in ["list files", "read file", "create folder", "write file", "delete file"]):
        return "files"
    if any(w in t for w in ["remember", "recall", "forget", "memory", "yaad"]):
        return "memory"
    if any(w in t for w in ["run code", "execute", "python"]):
        return "code"
    if any(w in t for w in ["weather", "news", "latest", "current", "today's"]):
        return "live_info"
    if any(w in t for w in ["system status", "cpu", "ram", "battery", "time", "date"]):
        return "system_info"
    # Check for smart write intent BEFORE generic automation
    if SMART_WRITE_OK and any(t.startswith(w) for w in
        ("write", "compose", "create", "make", "generate", "draft", "prepare", "likh", "bana")):
        if parse_write_intent(t) is not None:
            return "smart_write"
    if any(w in t for w in ["type ", "press ", "copy", "paste", "select all", "screenshot"]):
        return "automation"
    if any(w in t for w in ["complete task", "do task", "autonomous"]):
        return "autonomous"
    return "llm"

# ══════════════════════════════════════════════
# COMMAND HANDLERS
# ══════════════════════════════════════════════

def handle_smart_write_command(text: str):
    """
    Handles all natural language write/compose/create commands.
    Parses intent, generates full content via LLM, opens app, types it.
    Examples:
      'write essay on climate change on notepad'
      'write python code to reverse a string'
      'compose an email about the project'
      'make a to-do list for tomorrow'
      'write a poem about rain in vs code'
    """
    if not SMART_WRITE_OK:
        return None
    try:
        # Quick check so we don't intercept unrelated commands
        if parse_write_intent(text) is None:
            return None
        speak_async("Generating content… ek second 📝", "thinking")
        result = handle_smart_write(text)
        return result
    except Exception as e:
        return f"Content generate karne mein error: {e}"


def handle_web_commands(text: str):
    t = text.lower()
    if not WEB_OK:
        return None

    if "youtube" in t:
        # ✅ BUG FIX #5: Now using web_control2.search_youtube exclusively
        query = re.sub(r"(search|play|find|on|youtube)", "", t).strip()
        search_youtube(query or "music")
        return f"YouTube pe '{query or 'music'}' search kar rahi hoon 🎬"
    if "google" in t:
        query = re.sub(r"(search|find|on|google)", "", t).strip()
        search_google(query)
        return f"Google pe '{query}' dhoondh rahi hoon 🔍"
    if "scroll down" in t or "neeche scroll" in t:
        scroll_down()
        return "Neeche scroll kar diya ⬇️"
    if "scroll up" in t or "upar scroll" in t:
        scroll_up()
        return "Upar scroll kar diya ⬆️"
    if t.startswith("type "):
        content = text[5:].strip()
        write_text(content)
        return f"Likha diya ✍️"
    # Note: "write " prefix is intentionally NOT handled here anymore.
    # It is routed to handle_smart_write_command which generates real content.
    if "open website" in t:
        url = re.sub(r"open website", "", t).strip()
        open_website(url)
        return f"{url} khola 🌐"
    if "click link" in t:
        link = re.sub(r"click link", "", t).strip()
        click_link(link)
        return f"'{link}' pe click kar diya 🖱️"
    if "start browser" in t:
        return start_browser()
    return None

# =========================
# WHATSAPP INIT
# =========================
try:
    wa_handler = WhatsAppCommandHandler(ai_instance=None, headless=False)
    if wa_handler.start():
        print("[ROSY] WhatsApp connected ✓")
    else:
        print("[ROSY] WhatsApp not connected (scan QR)")
except Exception as e:
    print("[ROSY] WhatsApp init error:", e)
    wa_handler = None
   
def handle_screen_commands(text: str):
    if not SCREEN_VISION_OK:
        return None
    t = text.lower()
    if "read screen" in t or "what is on screen" in t or "screen mein kya hai" in t:
        try:
            info = describe_screen()
            return (
                f"Screen par {info.get('windows_detected',0)} windows aur "
                f"{info.get('objects_detected',0)} objects hain. "
                f"Text: {info.get('visible_text','')[:150]}"
            )
        except Exception as e:
            return f"Screen read error: {e}"
    if "click to" in t or "click on text" in t:
        target = re.sub(r"click (to|on text)", "", t).strip()
        ok = smart_click(target)
        return f"'{target}' pe click kar diya ✅" if ok else f"'{target}' screen par nahi mila ❌"
    if "read screen text" in t:
        return "Screen text: " + read_screen_text()[:300]
    if "detect objects" in t or "detect elements" in t:
        objs = detect_gui_elements()
        return f"{len(objs)} objects detect hue screen par."
    if "detect windows" in t:
        wins = detect_windows()
        return f"{len(wins)} windows detect hue."
    return None


def handle_automation_commands(text: str):
    if not AUTO_OK:
        return None
    t = text.lower()
    if "double click" in t:
        auto.double_click(); return "Double click kar diya ✅"
    if "right click" in t:
        auto.right_click(); return "Right click kar diya ✅"
    if "click mouse" in t or "click here" in t:
        auto.click(); return "Click kar diya ✅"
    if "move mouse" in t:
        nums = re.findall(r"\d+", t)
        if len(nums) >= 2:
            auto.move_mouse(int(nums[-2]), int(nums[-1]))
            return f"Mouse {nums[-2]},{nums[-1]} par move kar diya ✅"
    if t.startswith("type "):
        auto.type_text(text[5:]); return "Text type kar diya ✍️"
    if "press enter" in t:
        auto.press_key("enter"); return "Enter press kar diya ✅"
    if "press escape" in t:
        auto.press_key("esc"); return "Escape press kar diya ✅"
    if "press tab" in t:
        auto.press_key("tab"); return "Tab press kar diya ✅"
    if "copy" in t and "clipboard" not in t:
        auto.hotkey("ctrl", "c"); return "Copy kar diya ✅"
    if "paste" in t:
        auto.hotkey("ctrl", "v"); return "Paste kar diya ✅"
    if "select all" in t:
        auto.hotkey("ctrl", "a"); return "Sab select kar liya ✅"
    if "undo" in t:
        auto.hotkey("ctrl", "z"); return "Undo kar diya ↩️"
    if "scroll down" in t:
        auto.scroll(-500); return "Neeche scroll kar diya ⬇️"
    if "scroll up" in t:
        auto.scroll(500); return "Upar scroll kar diya ⬆️"
    if "take screenshot" in t or "screenshot lo" in t:
        fname = f"screenshot_{int(time.time())}.png"
        try:
            auto.screenshot(path=fname)
        except Exception:
            import pyautogui
            pyautogui.screenshot(fname)
        return f"Screenshot liya: {fname} 📸"
    if "open run" in t:
        auto.open_run(); return "Run dialog khola ✅"
    if "open start menu" in t:
        auto.open_start_menu(); return "Start menu khola ✅"
    return None


def handle_music_commands(text: str):
    if not MUSIC_OK:
        return None
    t = text.lower()
    if "play latest song" in t or "latest music" in t:
        return play_latest_songs()
    if "play next song" in t or "next video" in t or "next song" in t or "agla gaana" in t:
        return next_video()
    if "previous song" in t or "prev song" in t or "pichla gaana" in t:
        return prev_video()
    if "pause music" in t or "pause song" in t or "music pause" in t:
        return pause_play()
    if "increase volume" in t or "volume badhao" in t or "awaz badhao" in t:
        return volume_up()
    if "decrease volume" in t or "volume kam karo" in t or "awaz kam karo" in t:
        return volume_down()
    if "play first video" in t or "first video" in t:
        return play_first_youtube()
    if "mute volume" in t or "volume stop" in t or "awaz band karo" in t:
        return mute_volume()
    if "pause video" in t or "video pause karo" in t:
        return youtube_play_pause()
    if "next video" in t or "play next video" in t:
        return youtube_next()
    if t.startswith("play song "):
        return play_song(text[10:].strip())
    if t.startswith("search song "):
        return search_song(text[12:].strip())
    if "play music" in t:
        return play_latest_songs()
    # Mood-based
    for mood in ["happy", "sad", "romantic", "party", "focus", "relax", "workout", "morning"]:
        if mood in t and ("song" in t or "music" in t or "gaana" in t or "play" in t):
            return play_mood_songs(mood)
    # Language-based
    for lang in ["hindi", "english", "punjabi", "tamil", "telugu"]:
        if lang in t and ("song" in t or "music" in t or "play" in t):
            return play_by_language(lang)
    # Artist
    m = re.search(r"play (.+?)(?:songs?|music|ke gaane)", t)
    if m:
        artist = m.group(1).strip()
        if artist and len(artist) > 2:
            return play_artist(artist)
    # History
    if "song history" in t or "recently played" in t or "kya bajaya" in t:
        return get_play_history()
    # Generic play
    if "play " in t:
        song = re.sub(r"^play\s+", "", t).strip()
        return play_song(song)
    return None


def handle_file_commands(text: str):
    t = text.lower()
    if "list files" in t:
        path = re.sub(r"list files(?: in)?", "", t).strip() or "."
        try:
            files = list_files(path)
            return f"Files in '{path}': {', '.join(files[:20])}"
        except Exception as e:
            return str(e)
    if "read file" in t:
        name = re.sub(r"read file", "", t).strip()
        return read_file(name)[:500]
    if "create folder" in t:
        name = re.sub(r"create folder", "", t).strip()
        return create_folder(name)
    if "write file" in t or "create file" in t:
        # Pattern: write file <name> with content <...>
        m = re.search(r"(?:write|create) file (\S+) (?:with content|content) (.+)", text, re.I)
        if m:
            fname, content = m.group(1), m.group(2)
            return write_file(fname, content)
    if "delete file" in t:
        name = re.sub(r"delete file", "", t).strip()
        return delete_file(name)
    return None


def handle_memory_commands(text: str):
    t = text.lower()

    # ✅ BUG FIX #4 & #7: Unified memory using memory_system only
    # Remembering with key=value
    if "remember" in t:
        # Pattern: "remember that X is Y" or "remember X = Y"
        m = re.search(r"remember (?:that\s+)?(.+?)\s+(?:is|=)\s+(.+)", text, re.I)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            return remember(key, val)
        # Single value pattern: "remember that I love Python"
        data = re.sub(r"remember that|remember", "", text, flags=re.I).strip()
        if data:
            return remember(data)
        return "Kya yaad karna hai?"

    if "what do you remember about" in t:
        q = re.sub(r"what do you remember about", "", t).strip()
        return recall(q)

    if "what is my" in t:
        key = re.sub(r"what is my", "", t).strip()
        return recall(key)

    if "what is" in t and "?" in text:
        key = re.sub(r"what is", "", t).replace("?", "").strip()
        val = recall(key)
        if val and "yaad nahi" not in val:
            return val

    if "forget" in t:
        key = re.sub(r"forget", "", t).strip()
        return forget(key)

    if "list my memories" in t or "kya yaad hai" in t:
        mems = list_memories()
        if not mems:
            return "Koi memory nahi hai abhi."
        lines = [f"• {k}: {v}" for k, v in mems[:10]]
        return "Memories:\n" + "\n".join(lines)

    return None


def handle_code_commands(text: str):
    t = text.lower()
    if "run code" in t or "execute code" in t:
        code = re.sub(r"(run|execute) code", "", text).strip()
        if code:
            return run_python(code)
    if "run python" in t:
        code = re.sub(r"run python", "", text).strip()
        return run_python(code)
    return None


def handle_whatsapp_commands(text: str):
    # ✅ BUG FIX: was using undefined 'wa', now correctly uses 'wa_handler'
    if wa_handler is None:
        return None
    t = text.lower()

    # ✅ BUG FIX: replaced undefined 'wa' with 'wa_handler.plugin'
    # Route via wa_handler which handles natural language parsing
    if any(kw in t for kw in ["send", "message to", "whatsapp to", "msg to",
                               "bhejna", "bhejo", "likho", "send to"]):
        result = wa_handler.handle(text)
        if result:
            return result

    if t.startswith("read whatsapp "):
        name = text[len("read whatsapp "):].strip()
        return wa_handler.plugin.read_pretty(name, 10)

    if any(kw in t for kw in ["who messaged", "check whatsapp", "unread", "new messages",
                               "kya message", "kisne message"]):
        return wa_handler.plugin.who_messaged()

    if t.startswith("reply to "):
        try:
            m = re.match(r'reply to\s+([^"]+?)\s+"([^"]+)"\s+to\s+"([^"]+)"', text, re.I)
            if m:
                name, reply_text, target = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
                ok = wa_handler.plugin.wa.reply_to_message(name, target, reply_text) \
                     if hasattr(wa_handler.plugin, 'wa') else False
                return "Reply bhej diya 💬" if ok else "Reply nahi gayi 😕"
            return 'Format: reply to NAME "reply text" to "target message"'
        except Exception as e:
            return f"Reply error: {e}"

    # Final fallback: try the smart NL handler
    result = wa_handler.handle(text)
    return result if result else None


def handle_visual_ai(text: str):
    if not YOLO_OK:
        return None
    t = text.lower()

    if "detect objects" in t:
        objs = detect_objects()
        if not objs:
            return "Koi object detect nahi hua."
        names = list({o["name"] for o in objs})
        return f"Screen par: {', '.join(names[:10])}"

    if "click object" in t or "click on object" in t:
        target = re.sub(r"click (on )?object", "", t).strip()
        objs = detect_objects()
        for o in objs:
            if target in o["name"].lower():
                if AUTO_OK:
                    auto.move_mouse(o["x"], o["y"])
                    auto.click()
                return f"'{target}' par click kar diya ✅"
        return f"'{target}' nahi mila screen par ❌"

    return None


def handle_autonomous_task(command: str):
    t = command.lower()

    # Open apps
    if "open vscode" in t or "open visual studio code" in t:
        if AUTO_OK:
            auto.open_run(); time.sleep(0.8); auto.type_text("code"); auto.press_key("enter")
        return "VS Code khola ✅"
    if "open notepad" in t:
        if AUTO_OK:
            auto.open_run(); time.sleep(0.8); auto.type_text("notepad"); auto.press_key("enter")
        return "Notepad khola ✅"

    # Write code
    if "write hello world" in t:
        if AUTO_OK:
            auto.type_text('print("Hello, World!")')
        return "Hello World code likha ✅"

    # Save file
    if "save file" in t:
        if AUTO_OK:
            auto.hotkey("ctrl", "s"); time.sleep(0.5)
            fname = re.search(r"as (.+)", t)
            auto.type_text(fname.group(1) if fname else "untitled.py")
            auto.press_key("enter")
        return "File save kar di ✅"

    # Run code
    if "run program" in t or "run code" in t:
        if AUTO_OK:
            auto.hotkey("ctrl", "`"); time.sleep(0.8)
            auto.type_text("python main.py"); auto.press_key("enter")
        return "Program run kar diya ▶️"

    return None


def visual_agent(command: str):
    if not SCREEN_VISION_OK:
        return None
    t = command.lower()
    if "find and click" in t:
        target = re.sub(r"find and click", "", t).strip()
        ok = smart_click(target)
        return f"'{target}' par click kar diya ✅" if ok else f"'{target}' nahi mila ❌"
    if "what do you see" in t or "screen par kya hai" in t:
        info = describe_screen()
        return (
            f"Screen par {info.get('objects_detected',0)} objects aur "
            f"{info.get('windows_detected',0)} windows dikh rahe hain."
        )
    return None


def desktop_agent(command: str):
    steps = plan_task(command)
    if not steps:
        return None
    execute_task_chain(steps)
    return "Task complete ✅"


# ══════════════════════════════════════════════
# MASTER ROUTER (single pass, no duplicates)
# ✅ BUG FIX #9: Eliminated duplicate handler calls from main loop
# ══════════════════════════════════════════════
HANDLER_CHAIN = [
    ("pc_control",   handle_command),
    ("screen",       handle_screen_commands),
    ("smart_write",  handle_smart_write_command),
    ("automation",   handle_automation_commands),
    ("music",        handle_music_commands),
    ("web",          handle_web_commands),
    ("files",        handle_file_commands),
    ("memory",       handle_memory_commands),
    ("code",         handle_code_commands),
    ("whatsapp",     handle_whatsapp_commands),
    ("visual_ai",    handle_visual_ai),
    ("visual_agent", visual_agent),
    ("auto_task",    handle_autonomous_task),
    ("desktop",      desktop_agent),
]

def route_command(text: str):
    """Route text through all handlers. Return first match or None."""
    intent = classify_intent(text)
    
    # Fast-path: try the likely handler first
    priority_map = {
        "pc_control":  ["pc_control", "automation"],
        "screen":      ["screen", "visual_ai", "visual_agent"],
        "music":       ["music"],
        "web":         ["web"],
        "files":       ["files"],
        "memory":      ["memory"],
        "code":        ["code"],
        "whatsapp":    ["whatsapp"],
        "smart_write": ["smart_write"],
        "automation":  ["automation"],
        "autonomous":  ["auto_task", "desktop"],
    }

    tried = set()
    # Try priority handlers first
    for name in priority_map.get(intent, []):
        for hname, handler in HANDLER_CHAIN:
            if hname == name:
                try:
                    result = handler(text)
                    if result:
                        return result
                    tried.add(hname)
                except Exception as e:
                    print(f"[ROSY] Handler '{hname}' error: {e}")

    # Then try all remaining handlers
    for hname, handler in HANDLER_CHAIN:
        if hname in tried:
            continue
        try:
            result = handler(text)
            if result:
                return result
        except Exception as e:
            print(f"[ROSY] Handler '{hname}' error: {e}")

    return None  # Falls through to LLM


# ══════════════════════════════════════════════
# LLM ROUTER (smart model selection)
# ══════════════════════════════════════════════
def get_llm_response(user_input: str, history: str) -> str:
    t = user_input.lower()

    # Live data → Gemini (web access) or Perplexity
    if any(w in t for w in ["news", "weather", "latest", "current", "today", "aaj", "abhi"]):
        try:
            return ask_gemini(
                f"Current info needed. {user_input}\n"
                f"Reply in same language as question. Keep it brief."
            )
        except Exception:
            return ask_perplexity(
                f"Current info needed. {user_input}\n"
                f"Reply in same language as question. Keep it brief."
            )
        except:
            pass

    # Complex reasoning → Gemini
    if any(w in t for w in ["explain", "why", "how does", "difference", "compare", "analyze"]):
        try:
            return ask_gemini(
                f"Context:\n{history}\n\nQuestion: {user_input}\n"
                f"Reply briefly in same language."
            )
        except Exception:
            return ask_perplexity(
                f"Context:\n{history}\n\nQuestion: {user_input}\n"
                f"Reply briefly in same language."
                )
        except:
            pass

    # Default → Local Mistral
    if MISTRAL_AVAILABLE:
        reply = ""
        for token in generate_stream(user_input, history):
            reply += token
        return reply.strip()

    # Fallback → Gemini
    return ask_gemini(
        f"You are ROSY, an advanced AI assistant.\n"
        f"History:\n{history}\n\nUser: {user_input}\n"
        f"Reply briefly."
    )


# ══════════════════════════════════════════════
# VISUAL SCREEN AGENT
# ══════════════════════════════════════════════
def act_on_screen(command: str):
    """Look at screen, decide action, execute."""
    state = get_state()
    if not state:
        speak_async("Screen ka state nahi mila.", "sad")
        return

    action = think(command, state)
    print(f"[ROSY] Screen action: {action}")

    try:
        al = action.lower()
        if "click" in al and AUTO_OK:
            nums = re.findall(r"\d+", action)
            if len(nums) >= 2:
                click(int(nums[-2]), int(nums[-1]))
        elif "type" in al and AUTO_OK:
            type_text(action.replace("type", "").strip())
        elif "scroll" in al and AUTO_OK:
            auto.scroll(-500 if "down" in al else 500)
        elif "open" in al:
            result = handle_command(action)
            if result:
                speak_async(result, "happy")
    except Exception as e:
        print(f"[ROSY] act_on_screen error: {e}")


# ══════════════════════════════════════════════
# AUTONOMOUS AGENT LOOP
# ══════════════════════════════════════════════
def run_autonomous_agent(goal: str):
    speak_async("Autonomous mode. Planning...", "thinking")

    handlers = [
        route_command,
        handle_command,
        handle_web_commands,
        handle_screen_commands,
    ]

    try:
        steps = plan(goal)
    except Exception:
        steps = [goal]

    for i, step in enumerate(steps, 1):
        try:
            print(f"[ROSY] Step {i}/{len(steps)}: {step}")
            result = act(step, handlers)
            if result:
                speak_async(result, "happy")

            if SCREEN_VISION_OK:
                observation = observe()
                correction = self_correct(goal, step, observation)
                if "done" in correction.lower():
                    speak_async("Goal achieved. ✅", "happy")
                    return
                goal = correction

        except Exception as e:
            err = traceback.format_exc()
            print(f"[ROSY] Step error: {err}")
            try:
                fix = improve_code(step, err)
                print(f"[ROSY] Suggested fix:\n{fix}")
            except Exception:
                pass
            speak_async("Encountered an error. Attempting recovery.", "sad")

    speak_async("Autonomous task complete.", "caring")


# ══════════════════════════════════════════════
# SAVE TARGET HELPER (BUG FIX #8)
# ✅ BUG FIX: Was opening vision_memory.json without checking existence
# ══════════════════════════════════════════════
def save_target(name: str, pos: tuple):
    VFILE = "vision_memory.json"
    data = {}
    if os.path.exists(VFILE):
        try:
            with open(VFILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[name] = pos
    with open(VFILE, "w") as f:
        json.dump(data, f, indent=2)


# ══════════════════════════════════════════════
# SMART ACTION (visual click)
# ══════════════════════════════════════════════
def smart_action(command: str):
    t = command.lower()
    target = re.sub(r"(click|open|find)", "", t).strip()
    pos = find_target(target)
    if pos and AUTO_OK:
        x, y = pos
        click(x, y)
        return f"Clicked '{target}' ✅"
    if "type" in t and AUTO_OK:
        content = re.sub(r"type", "", t).strip()
        type_text(content)
        return f"Typed '{content}' ✍️"
    return f"Could not find '{target}' on screen ❌"


# ══════════════════════════════════════════════
# STARTUP REPORT
# ══════════════════════════════════════════════
def startup_report():
    now = datetime.datetime.now()
    h = now.hour
    greet = "Good morning" if h < 12 else "Good afternoon" if h < 17 else "Good evening"
    stats = get_system_stats()
    
    report = (
        f"{greet}. ROSY online. "
        f"{stats}. "
        f"All systems ready. How can I assist?"
    )
    print(f"\n{'='*60}")
    print(f"  ROSY AI — {now.strftime('%d %B %Y, %I:%M %p')}")
    print(f"{'='*60}")
    print(f"  {stats}")
    print(f"{'='*60}\n")
    speak_async(report, "caring")


# ══════════════════════════════════════════════
# QUICK RESPONSES (no LLM needed)
# ══════════════════════════════════════════════
QUICK_RESPONSES = {
    "how are you":       "All systems operational. Thanks for asking.",
    "how r u":           "Running at peak efficiency.",
    "who are you":       "I am ROSY — your advanced AI assistant, built by Prince.",
    "what are you doing":"Monitoring systems and waiting for your command.",
    "what can you do":   (
        "I can control your PC, browse the web, play music, "
        "send WhatsApp messages, manage files, execute code, "
        "read your screen, and have intelligent conversations."
    ),
    "what is your name": "ROSY. Just A Rather Very Intelligent System.",
    "good morning":      "Good morning. Systems fully operational.",
    "good night":        "Good night. I'll be here when you need me.",
    "thank you":         "Anytime.",
    "thanks":            "Always here to help.",
    "bye":               "Farewell. All systems will remain on standby.",
    "stop":              None,  # handled separately
}

def check_quick_response(text: str):
    tl = text.lower().strip().rstrip("?.!")
    for key, resp in QUICK_RESPONSES.items():
        if key in tl:
            return resp
    return None


# ══════════════════════════════════════════════
# REMINDER SYSTEM (simple async)
# ══════════════════════════════════════════════
_reminders = []

def add_reminder(message: str, seconds: int):
    def _remind():
        time.sleep(seconds)
        speak_async(f"Reminder: {message}", "happy")
        print(f"\n[ROSY REMINDER] {message}\n")
    t = threading.Thread(target=_remind, daemon=True)
    t.start()
    _reminders.append(message)


def handle_reminder(text: str):
    # Pattern: "remind me in 5 minutes to <task>"
    m = re.search(
        r"remind me in (\d+)\s*(minute|minutes|second|seconds|hour|hours)\s+(?:to\s+)?(.+)",
        text, re.I
    )
    if m:
        amount = int(m.group(1))
        unit   = m.group(2).lower()
        task   = m.group(3).strip()
        secs = amount * (60 if "minute" in unit else 3600 if "hour" in unit else 1)
        add_reminder(task, secs)
        return f"Reminder set: '{task}' in {amount} {unit} ⏰"

    m2 = re.search(r"(?:set|add) (?:a )?reminder (?:for\s+)?(.+)", text, re.I)
    if m2:
        return f"Say: 'remind me in 5 minutes to {m2.group(1)}'"

    return None


# ══════════════════════════════════════════════
#  MAIN LOOP
# ══════════════════════════════════════════════
def main():
    global COMMAND_COUNT
    startup_report()

    print("[ROSY] Waiting for wake word…\n")

    while True:
        # ── SLEEP: wait for "Hey Rosy" / "Hey ROSY" ──
        wait_for_wake_word()
        print("[ROSY] Activated ✓")
        speak_async(_get_greeting(), "caring")

        # ── ACTIVE SESSION ──
        while True:
            user_input = listen()
            if not user_input:
                continue
            # =========================
            # ✅ BUG FIX: result was used outside its if-block → NameError
            #    crashed silently → except → continue → skipped ALL commands
            if wa_handler:
                try:
                    if wa_handler.is_whatsapp_command(user_input):
                        result = wa_handler.handle(user_input)
                        if result:
                            print(result)
                            speak_async(result)
                        continue   # only skip further processing for WA commands
                except Exception as e:
                    speak_async(f"WhatsApp error: {e}")
                    continue
            COMMAND_COUNT += 1
            low = user_input.lower().strip()
            print(f"\n[You #{COMMAND_COUNT}] {user_input}")

            # ── Go to sleep ──
            if any(x in low for x in ["go to sleep", "bye ROSY", "goodbye ROSY", "so jao", "bye rosy"]):
                speak_async("Standing by. Call me when needed.", "caring")
                break

            # ── Hard stop ──
            if "stop" in low or "stop talking" in low or "chup" in low:
                stop_speaking()
                continue

            # ── Stop vision ──
            if "stop everything" in low:
                stop_vision()
                speak_async("All actions stopped.", "sad")
                continue

            # ── Exit program ──
            if low in ["exit", "exit ROSY", "quit", "shutdown ROSY"]:
                speak_async("ROSY shutting down. Goodbye.", "caring")
                sys.exit(0)

            # ── Screen action mode ──
            if any(x in low for x in ["on screen", "do on screen", "see screen", "screen par karo"]):
                speak_async("Scanning screen…", "thinking")
                act_on_screen(user_input)
                continue

            # ── Smart visual click ──
            if any(x in low for x in ["click on", "find and click", "click the"]):
                speak_async("Looking…", "thinking")
                result = smart_action(user_input)
                speak_async(result, detect_tone(result))
                continue

            # ── Reminder ──
            rem = handle_reminder(user_input)
            if rem:
                speak_async(rem, "happy")
                print(f"[ROSY] {rem}")
                continue

            # ── Autonomous task mode ──
            if any(x in low for x in ["complete task", "do task", "autonomous mode", "auto task"]):
                goal = re.sub(r"(complete task|do task|autonomous mode|auto task)", "", user_input).strip()
                threading.Thread(target=run_autonomous_agent, args=(goal,), daemon=True).start()
                continue

            # ── Quick response (no LLM needed) ──
            quick = check_quick_response(user_input)
            if quick:
                speak_async(quick, detect_tone(quick))
                print(f"[ROSY] {quick}")
                continue

            # ── System info (fast path) ──
            if any(x in low for x in ["system status", "status report", "how is the system"]):
                stats = get_system_stats()
                speak_async(stats, "caring")
                print(f"[ROSY] {stats}")
                continue

            # ── Route through all handlers ──
            result = route_command(user_input)
            if result:
                result = _naturalise(result)
                tone = detect_tone(result)
                speak_async(result, tone)
                print(f"[ROSY] {result}")
                continue

            # ── Task words: plan first ──
            TASK_WORDS = ["open ", "close ", "launch ", "download ", "install "]
            if any(low.startswith(x) for x in TASK_WORDS):
                steps = plan_task(user_input)
                if steps:
                    execute_task_chain(steps)
                    continue

            # ── LLM response ──
            memory.add_user(user_input)
            speak_async(random.choice(ROSY_FILLERS), "thinking")

            try:
                reply = get_llm_response(user_input, memory.get())
            except Exception as e:
                reply = f"Processing error: {e}"

            if reply:
                reply = _naturalise(reply.strip())
                memory.add_assistant(reply)
                tone = detect_tone(reply)
                speak_async(reply, tone)
                print(f"[ROSY] {reply}")


if __name__ == "__main__":
    main()
