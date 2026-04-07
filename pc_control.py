import os
import json
import webbrowser
import subprocess
import platform
import psutil
import datetime

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
PROTECTED_PROCESSES = {
    "explorer.exe", "svchost.exe", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "smss.exe", "system", "idle"
}

APP_DB = "apps.json"
LEARNED_APPS: dict = {}

if os.path.exists(APP_DB):
    try:
        with open(APP_DB, "r", encoding="utf-8") as f:
            LEARNED_APPS = json.load(f)
    except Exception:
        pass


def _save_apps():
    with open(APP_DB, "w", encoding="utf-8") as f:
        json.dump(LEARNED_APPS, f, indent=4)


# App path helper — reads from env first, then fallback
def _app(env_var: str, fallback: str) -> str:
    return os.environ.get(env_var, fallback)


# ─────────────────────────────────────────────
# Close any app safely
# ─────────────────────────────────────────────
def close_any_app(app_name: str) -> bool:
    closed = False
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pname = (proc.info["name"] or "").lower()
            if pname in PROTECTED_PROCESSES:
                continue
            if app_name.lower() in pname:
                proc.terminate()
                closed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return closed


# ─────────────────────────────────────────────
# System info
# ─────────────────────────────────────────────
def get_system_stats() -> str:
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    ram_used = ram.used // (1024 ** 3)
    ram_total = ram.total // (1024 ** 3)
    now = datetime.datetime.now().strftime("%I:%M %p, %d %B %Y")

    stats = [f"Time: {now}", f"CPU: {cpu}%", f"RAM: {ram_used}/{ram_total} GB"]

    try:
        batt = psutil.sensors_battery()
        if batt:
            plug = "charging" if batt.power_plugged else "on battery"
            stats.append(f"Battery: {int(batt.percent)}% ({plug})")
    except Exception:
        pass

    try:
        disk = psutil.disk_usage("C:\\")
        free_gb = disk.free // (1024 ** 3)
        stats.append(f"C: Drive Free: {free_gb} GB")
    except Exception:
        pass

    return " | ".join(stats)


# ─────────────────────────────────────────────
# Volume control (Windows)
# ─────────────────────────────────────────────
def set_volume(level: int):
    """Set master volume 0-100."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        scalar = max(0.0, min(1.0, level / 100.0))
        volume.SetMasterVolumeLevelScalar(scalar, None)
        return f"Volume {level}% set kar diya 🔊"
    except ImportError:
        # Fallback via nircmd
        try:
            nircmd = r"C:\nircmd\nircmd.exe"
            if os.path.exists(nircmd):
                vol = int(65535 * level / 100)
                os.system(f'"{nircmd}" setsysvolume {vol}')
                return f"Volume {level}% set kar diya 🔊"
        except Exception:
            pass
        return "Volume control ke liye pycaw install karein"


def volume_up():
    try:
        import pyautogui
        pyautogui.press("volumeup", presses=10)
        return "Volume badha diya 🔊"
    except Exception as e:
        return f"Volume up error: {e}"


def volume_down():
    try:
        import pyautogui
        pyautogui.press("volumedown", presses=10)
        return "Volume ghata diya 🔉"
    except Exception as e:
        return f"Volume down error: {e}"


def mute_volume():
    try:
        import pyautogui
        pyautogui.press("volumemute")
        return "Volume mute kar diya 🔇"
    except Exception as e:
        return f"Mute error: {e}"


# ─────────────────────────────────────────────
# Clipboard
# ─────────────────────────────────────────────
def get_clipboard() -> str:
    try:
        import pyperclip
        return pyperclip.paste() or "(clipboard empty)"
    except Exception:
        return "pyperclip nahi mila"


def set_clipboard(text: str) -> str:
    try:
        import pyperclip
        pyperclip.copy(text)
        return f"'{text[:40]}' clipboard mein copy kar diya"
    except Exception as e:
        return f"Clipboard error: {e}"


# ─────────────────────────────────────────────
# Main command handler
# ─────────────────────────────────────────────
APPS = {
    "chrome":      _app("CHROME_PATH",     "chrome"),
    "notepad":     "notepad.exe",
    "calculator":  "calc.exe",
    "cmd":         "cmd.exe",
    "powershell":  "powershell.exe",
    "paint":       "mspaint.exe",
    "vscode":      _app("VSCODE_PATH",     r"D:\Microsoft VS Code\Code.exe"),
    "word":        _app("WORD_PATH",       r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"),
    "excel":       _app("EXCEL_PATH",      r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"),
    "edge":        _app("EDGE_PATH",       r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Microsoft Edge.lnk"),
    "audacity":    _app("AUDACITY_PATH",   r"C:\Program Files\Audacity\audacity.exe"),
    "blender":     _app("BLENDER_PATH",    r"C:\Program Files\Blender Foundation\Blender 4.5\blender-launcher.exe"),
    "whatsapp":    _app("WHATSAPP_PATH",   r"C:\Program Files\WindowsApps\5319275A.WhatsAppDesktop_2.2587.10.0_x64__cv1g1gvanyjgm\WhatsApp.Root.exe"),
    "nvidia":      _app("NVIDIA_APP_PATH", r"C:\Program Files\NVIDIA Corporation\NVIDIA App\CEF\NVIDIA App.exe"),
    "spotify":     _app("SPOTIFY_PATH",    os.path.expanduser(r"~\AppData\Roaming\Spotify\Spotify.exe")),
    "telegram":    _app("TELEGRAM_PATH",   os.path.expanduser(r"~\AppData\Roaming\Telegram Desktop\Telegram.exe")),
    "vlc":         _app("VLC_PATH",        r"C:\Program Files\VideoLAN\VLC\vlc.exe"),
    "explorer":    "explorer.exe",
    "taskmanager": "taskmgr.exe",
    "settings":    "ms-settings:",
    "optional features": "optionalfeatures.exe",
}

APP_ALIASES = {
    "visual studio code": "vscode",
    "vs code": "vscode",
    "microsoft edge": "edge",
    "ms edge": "edge",
    "command prompt": "cmd",
    "task manager": "taskmanager",
    "file explorer": "explorer",
    "ms office": "word",
    "office": "word",
    "ms excel": "excel",
}


def handle_command(text: str):
    t = text.lower().strip()

    # ─── System ───
    if "shutdown" in t:
        os.system("shutdown /s /t 10")
        return "PC 10 seconds mein shutdown ho raha hai 😴 (cancel: shutdown /a)"
    if "restart" in t or "reboot" in t:
        os.system("shutdown /r /t 10")
        return "PC restart ho raha hai 🔄"
    if "lock pc" in t or "lock system" in t:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "PC lock kar diya 🔒"
    if "sleep mode" in t or "hibernate" in t:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "PC sleep mode mein ja raha hai 😴"
    if "cancel shutdown" in t or "abort shutdown" in t:
        os.system("shutdown /a")
        return "Shutdown cancel kar diya ✅"

    # ─── System stats ───
    if any(x in t for x in ["system status", "cpu usage", "ram usage", "battery status", "system info"]):
        return get_system_stats()

    # ─── Volume ───
    if "volume up" in t or "volume badhao" in t or "volume jyada karo" in t:
        return volume_up()
    if "volume down" in t or "volume ghataao" in t or "volume kam karo" in t or "volume kam karo" in t:
        return volume_down()
    if "mute" in t:
        return mute_volume()
    if "set volume" in t or "volume karo" in t:
        import re
        nums = re.findall(r"\d+", t)
        if nums:
            return set_volume(int(nums[0]))

    # ─── Clipboard ───
    if "read clipboard" in t or "clipboard mein kya hai" in t or "kya copy hai" in t:
        return "Clipboard: " + get_clipboard()

    # ─── Time/Date ───
    if "time" in t and ("kya" in t or "what" in t or "batao" in t or "tell" in t):
        return datetime.datetime.now().strftime("Abhi %I:%M %p baj rahe hain")
    if "date" in t and ("kya" in t or "what" in t or "batao" in t or "tell" in t):
        return datetime.datetime.now().strftime("Aaj %d %B %Y hai")

    # ─── Web ───
    if "open youtube" in t:
        webbrowser.open("https://youtube.com")
        return "YouTube khol diya 🎥"
    if "open google" in t:
        webbrowser.open("https://google.com")
        return "Google open kar diya 🔍"
    if "open gmail" in t:
        webbrowser.open("https://mail.google.com")
        return "Gmail khol diya 📧"
    if "open github" in t:
        webbrowser.open("https://github.com")
        return "GitHub khol diya 💻"
    if "open instagram" in t:
        webbrowser.open("https://instagram.com")
        return "Instagram khol diya 📸"
    if "open twitter" in t or "open x" in t:
        webbrowser.open("https://x.com")
        return "Twitter/X khol diya 🐦"
    if "open linkedin" in t:
        webbrowser.open("https://linkedin.com")
        return "LinkedIn khol diya 💼"

    # ─── Resolve aliases ───
    for alias, canonical in APP_ALIASES.items():
        if alias in t:
            t = t.replace(alias, canonical)
            break

    # ─── Open apps ───
    for app_key, app_path in APPS.items():
        if f"open {app_key}" in t:
            try:
                os.startfile(app_path)
                return f"{app_key.title()} khol diya 💻"
            except Exception as e:
                # Try via subprocess
                try:
                    subprocess.Popen(app_path, shell=True)
                    return f"{app_key.title()} khol diya 💻"
                except Exception:
                    return f"{app_key} nahi khul raha: {e}"

    # ─── Close apps ───
    for app_key in APPS:
        close_aliases = [app_key, app_key.replace("exe", "").strip()]
        for alias in close_aliases:
            if f"close {alias}" in t or f"band karo {alias}" in t:
                if app_key.lower() in PROTECTED_PROCESSES:
                    return f"{app_key} system process hai, band nahi kar sakti 🚫"
                if close_any_app(app_key):
                    return f"{app_key.title()} band kar diya 📴"
                return f"{app_key} chal nahi raha tha 🤍"

    # ─── Learn new app ───
    if t.startswith("learn app "):
        try:
            parts = text.split(" ", 3)
            app_name = parts[2].lower()
            path = parts[3].strip() if len(parts) > 3 else ""
            if os.path.exists(path):
                LEARNED_APPS[app_name] = path
                APPS[app_name] = path
                _save_apps()
                return f"'{app_name}' yaad kar liya ✅ Ab bol sakte ho: open {app_name}"
            return "Path sahi nahi laga 😕"
        except Exception:
            return "Aise bolo: learn app <naam> <poora_path>"

    # ─── Learned apps ───
    for app_name, path in LEARNED_APPS.items():
        if f"open {app_name}" in t:
            if os.path.exists(path):
                os.startfile(path)
                return f"{app_name} khol diya 💖"
            return f"{app_name} ka path galat lagta hai 😕"

    # ─── Generic close ───
    if t.startswith("close "):
        name = t.replace("close ", "").strip()
        if name in PROTECTED_PROCESSES:
            return "Ye system process hai, band nahi kar sakti 🚫"
        if close_any_app(name):
            return f"{name} band kar diya 📴"
        return f"{name} chal nahi raha tha 🤍"

    return None
