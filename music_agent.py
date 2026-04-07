import os
import random
import requests

# ✅ BUG FIX: import from web_control2 (the correct, non-commented source)
try:
    from web_control2 import search_youtube
except ImportError:
    from web_control import search_youtube

try:
    from control.automation import press_key
    AUTO_OK = True
except ImportError:
    AUTO_OK = False

OFFLINE_MUSIC_FOLDER = os.environ.get(
    "MUSIC_FOLDER",
    os.path.expanduser("~/Music")
)

_play_history: list = []


# ═══════════════════════════════════════════════
# UTILS
# ═══════════════════════════════════════════════
def internet_available() -> bool:
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except Exception:
        return False


def _remember_played(name: str):
    _play_history.append(name)
    if len(_play_history) > 50:
        _play_history.pop(0)


def play_song(song_name: str) -> str:
    if internet_available():
        query = f"{song_name} full song"
        search_youtube(query)
        _remember_played(song_name)
        return f"'{song_name}' YouTube par chala rahi hoon 🎵"
    return play_offline_song(song_name)


def play_latest_songs(genre: str = "hindi") -> str:
    query = f"latest {genre} songs 2026"
    if internet_available():
        search_youtube(query)
        return f"Latest {genre} songs chala rahi hoon 🔥"
    return play_random_offline()


def play_mood_songs(mood: str) -> str:
    """Play music based on mood."""
    MOOD_QUERIES = {
        "happy":    "happy upbeat hindi songs",
        "sad":      "sad emotional hindi songs",
        "romantic": "romantic love songs hindi",
        "party":    "party dance songs hindi",
        "focus":    "lofi study beats",
        "relax":    "chill relaxing music instrumental",
        "workout":  "gym motivation songs",
        "morning":  "morning fresh songs hindi",
    }
    query = MOOD_QUERIES.get(mood.lower(), f"{mood} songs")
    if internet_available():
        search_youtube(query)
        return f"Tumhare mood ke liye {mood} songs chala raha hoon 🎶"
    return play_random_offline()


def search_song(query: str) -> str:
    search_youtube(f"{query} song")
    return f"'{query}' YouTube par search kar rahi hoon 🔍"


def play_artist(artist: str) -> str:
    search_youtube(f"{artist} songs playlist")
    return f"{artist} ke gaane chala rahi hoon 🎤"


def play_by_language(lang: str) -> str:
    queries = {
        "hindi":   "hindi hits songs",
        "english": "english pop hits",
        "punjabi": "punjabi songs",
        "tamil":   "tamil hits songs",
        "telugu":  "telugu hits songs",
    }
    q = queries.get(lang.lower(), f"{lang} songs")
    search_youtube(q)
    return f"{lang.title()} songs chala rahi hoon 🎵"


# ═══════════════════════════════════════════════
# PLAYBACK CONTROLS
# ═══════════════════════════════════════════════
def next_video() -> str:
    if AUTO_OK:
        press_key("shift+n")   # YouTube next shortcut
        return "Next song ▶️"
    return "Automation module nahi mila."


def prev_video() -> str:
    if AUTO_OK:
        press_key("shift+p")
        return "Previous song ◀️"
    return "Automation module nahi mila."


def pause_play() -> str:
    if AUTO_OK:
        press_key("k")   # YouTube play/pause
        return "Play/Pause toggle kar diya ⏯️"
    return "Automation module nahi mila."


def mute_song() -> str:
    if AUTO_OK:
        press_key("m")
        return "Song mute/unmute kar diya 🔇"
    return "Automation module nahi mila."


# ═══════════════════════════════════════════════
# OFFLINE FALLBACK
# ═══════════════════════════════════════════════
def _get_offline_songs() -> list:
    if not os.path.isdir(OFFLINE_MUSIC_FOLDER):
        return []
    exts = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}
    return [
        os.path.join(OFFLINE_MUSIC_FOLDER, f)
        for f in os.listdir(OFFLINE_MUSIC_FOLDER)
        if os.path.splitext(f)[1].lower() in exts
    ]


def play_offline_song(song_name: str) -> str:
    songs = _get_offline_songs()
    matches = [s for s in songs if song_name.lower() in os.path.basename(s).lower()]
    target = matches[0] if matches else (random.choice(songs) if songs else None)
    if target:
        try:
            os.startfile(target)
            return f"Offline: '{os.path.basename(target)}' chala rahi hoon 🎵"
        except Exception as e:
            return f"Offline play error: {e}"
    return "Internet nahi hai aur offline music folder bhi khaali hai 😕"


def play_random_offline() -> str:
    songs = _get_offline_songs()
    if not songs:
        return "Koi offline song nahi mila. Internet check karo 🌐"
    song = random.choice(songs)
    try:
        os.startfile(song)
        _remember_played(song)
        return f"Offline: '{os.path.basename(song)}' chala rahi hoon 🎵"
    except Exception as e:
        return f"Play error: {e}"


def get_play_history() -> str:
    if not _play_history:
        return "Abhi tak koi song nahi chala."
    recent = _play_history[-5:]
    return "Recently played: " + ", ".join(recent)
