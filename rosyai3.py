# =========================
# ROSY AI – MAIN FILE
# =========================
import traceback
from tts.sarvamai_tts2 import speak_async, stop_speaking
#from tts.emotional_tts import speak_streaming as offline_speak
from llm_mistral import generate_stream
from memory import Memory
from audioio import listen
from agent_brain import observe, think, plan, act, self_correct, improve_code
from vector_memory import remember, recall
from music_agent import play_song, play_latest_songs, next_video, search_song
from task_planner import plan_task
from task_executor import execute_task_chain
from screen_vision import (
    read_screen_text,
    smart_click,
    detect_gui_elements,
    detect_windows,
    describe_screen
)
from whatsapp_rosy import *
from whatsapp_command_handler import WhatsAppCommandHandler
import os
import dotenv
dotenv.load_dotenv()
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import urllib.parse
import json
from vision_loop import start_vision, stop_vision, get_state
import time
import webbrowser
from pc_control import handle_command
from vision_yolo import detect_objects
from control.automation import click, type_text
from agent_brain import think
from file_agent import list_files, read_file, create_folder
from camera_awarness import who_is_here
from web_control2 import (
    search_youtube,
    search_google,
    scroll_down,
    scroll_up,
    write_text,
    start_browser,
    open_website,
    google_search,
    click_link
)
from web_control import search_youtube, play_first_youtube, youtube_play_pause, youtube_next
from control import automation as auto
from code_executer import run_python
from memory_system import remember, recall
from ultra_vision import find_target
from wake_word import wait_for_wake_word
from external_llm import ask_gemini, ask_perplexity
import random
#from whatsapp_agent import get_whatsapp_agent
#try:
#    wa = get_whatsapp_agent(profile_dir=r"C:\Users\ravin\AppData\Local\Microsoft\Edge\User Data\rosy_whatsapp_profile")
#except Exception as e:
#    wa = get_whatsapp_agent()
#wa.open_whatsapp()
try:
    start_vision()
except Exception as e:
    print("Error starting vision:", e)

FILLERS = ["hmm…", "acha…", "suno…", "haan…", "ek second…"]

def humanize(text):
    if len(text) > 60:
        return f"{random.choice(FILLERS)} {text}"
    return text

# =========================
# GLOBAL STATE
# =========================
SESSION_AUTHENTICATED = False
memory = Memory()
# =========================
# WHATSAPP INIT
# =========================
try:
    wa_handler = WhatsAppCommandHandler(ai_instance=None, headless=False)
    if wa_handler.start():
        print("✅ WhatsApp connected")
    else:
        print("⚠️ WhatsApp not connected (scan QR manually)")
except Exception as e:
    print("❌ WhatsApp init error:", e)
    wa_handler = None
# =========================
# WEB COMMAND HANDLER
# =========================
def handle_web_commands(text):
    t = text.lower()

    if "youtube" in t:
        query = t.replace("youtube", "").replace("search", "").strip()
        search_youtube(query)
        return f"YouTube pe {query} chala rahi hoon 💖"
    if "google" in t:
        query = t.replace("google", "").replace("search", "").strip()
        search_google(query)
        return f"Google pe {query} dhoondh rahi hoon 🔍"

    if "scroll down" in t or "neeche scroll" in t:
        scroll_down()
        return "Neeche scroll kar diya ⬇️"

    if "scroll up" in t or "upar scroll" in t:
        scroll_up()
        return "Upar scroll kar diya ⬆️"

    if t.startswith("type "):
        write_text(text[5:])
        return "Likha diya ✍️"
    if t.startswith("write "):
        write_text(text[6:])
        return "Likha diya ✍️"
    if t.startswith("open website "):
        url = text.replace("open website", "").strip()
        open_website(url)
        return f"{url} khol diya 🌐"
    if t.startswith("search google for "):
        query = text.replace("search google for", "").strip()
        google_search(query)
        return f"Google pe {query} dhoondh rahi hoon 🔍"
    if t.startswith("click link "):
        link_text = text.replace("click link", "").strip()
        click_link(link_text)
        return f"{link_text} pe click kar diya 🖱️"
    if t.startswith("start browser"):
        start_browser()
        return "Browser khol diya 🌐"
    return None

# =========================
# AUTONOMOUS TASK EXECUTOR
# =========================

def execute_autonomous_task(command):

    cmd = command.lower()

    # open applications
    if "open vscode" in cmd or "open visual studio code" in cmd:
        auto.open_run()
        time.sleep(1)
        auto.type_text("code")
        auto.press_key("enter")
        return "VS Code khol diya."

    if "open notepad" in cmd:
        auto.open_run()
        time.sleep(1)
        auto.type_text("notepad")
        auto.press_key("enter")
        return "Notepad khol diya."

    if "open chrome" in cmd:
        auto.open_run()
        time.sleep(1)
        auto.type_text("chrome")
        auto.press_key("enter")
        return "Chrome khol diya."

    if "open calculator" in cmd:
        auto.open_run()
        time.sleep(1)
        auto.type_text("calc")
        auto.press_key("enter")
        return "Calculator khol diya."

    # write python code
    if "write hello world program" in cmd:

        code = """
print("Hello World")
"""

        auto.type_text(code)
        return "Python code likh diya."

    # save file
    if "save file" in cmd:

        auto.hotkey("ctrl","s")
        time.sleep(1)

        auto.type_text("hello.py")
        auto.press_key("enter")

        return "File save kar di."

    # run python code
    if "run program" in cmd or "run code" in cmd:

        auto.hotkey("ctrl","`")   # open terminal
        time.sleep(1)

        auto.type_text("python hello.py")
        auto.press_key("enter")

        return "Program run kar diya."

    return None
# =========================
# AUTOMATION VOICE CONTROL
# =========================

def handle_automation_commands(cmd):

    cmd = cmd.lower()

    # mouse click
    if "click mouse" in cmd or "click here" in cmd:
        auto.click()
        return "Click kar diya."

    if "double click" in cmd:
        auto.double_click()
        return "Double click kar diya."

    if "right click" in cmd:
        auto.right_click()
        return "Right click kar diya."

    # move mouse
    if "move mouse" in cmd:
        parts = cmd.split()
        try:
            x = int(parts[-2])
            y = int(parts[-1])
            auto.move_mouse(x, y)
            return f"Mouse {x},{y} par move kar diya."
        except:
            return "Coordinates samajh nahi aaye."

    # typing
    if cmd.startswith("type "):
        text = cmd.replace("type ", "")
        auto.type_text(text)
        return "Text likh diya."

    # keyboard
    if "press enter" in cmd:
        auto.press_key("enter")
        return "Enter press kar diya."

    if "press escape" in cmd:
        auto.press_key("esc")
        return "Escape press kar diya."

    if "copy" in cmd:
        auto.hotkey("ctrl", "c")
        return "Copy kar diya."

    if "paste" in cmd:
        auto.hotkey("ctrl", "v")
        return "Paste kar diya."

    if "select all" in cmd:
        auto.hotkey("ctrl", "a")
        return "Sab select kar diya."

    # scrolling
    if "scroll down" in cmd:
        auto.scroll(-500)
        return "Neeche scroll kar diya."

    if "scroll up" in cmd:
        auto.scroll(500)
        return "Upar scroll kar diya."

    # open run
    if "open run" in cmd:
        auto.open_run()
        return "Run dialog khol diya."

    # start menu
    if "open start menu" in cmd:
        auto.open_start_menu()
        return "Start menu khol diya."

    # screenshot
    if "take screenshot" in cmd:
        auto.screenshot(path="rosy_screen.png")
        return "Screenshot le liya."

    return None
def handle_screen_commands(command):

    cmd = command.lower()

    # read screen
    if "read screen" in cmd or "what is on screen" in cmd:
        info = describe_screen()

        return f"I can see {info['windows_detected']} windows and {info['objects_detected']} objects. Visible text: {info['visible_text'][:150]}"


    # click element
    if "click to" in cmd:

        words = cmd.split("click to")[-1].strip()

        success = smart_click(words)

        if success:
            return f"I clicked {words}"
        else:
            return f"I could not find {words} on screen"
    # detect windows
    if "detect windows" in cmd:

        windows = detect_windows()

        return f"I found {len(windows)} windows on your screen."
    # detect gui elements
    if "detect objects" in cmd or "detect elements" in cmd:

        objs = detect_gui_elements()

        return f"I detected {len(objs)} objects on screen."
    if "read screen text" in cmd:
        text = read_screen_text()
        return f"The visible text on the screen is: {text[:200]}"


    return None

def handle_advanced_commands(cmd):

    cmd = cmd.lower()

    # memory
    if "remember" in cmd:
        parts = cmd.replace("remember","").split(" is ")
        if len(parts)==2:
            return remember(parts[0].strip(),parts[1].strip())

    if "what is my" in cmd:
        key = cmd.replace("what is my","").strip()
        val = recall(key)
        return val if val else "Mujhe Yaad Nahi Hai."
    if "what is" in cmd:
        key = cmd.replace("what is","").strip()
        val = recall(key)
        return val if val else "Mujhe Yaad Nahi Hai."

    # browser
    if "search" in cmd:
        query = cmd.replace("search","")
        return google_search(query)

    if "run code" in cmd:
        code = cmd.replace("run code","")
        return run_python(code)

    return None

def handle_music_commands(text):

    low = text.lower()

    if "play latest song" in low or "latest music" in low:
        return play_latest_songs()

    if "play next song" in low or "next video" in low:
        return next_video()

    if low.startswith("play song "):
        song = text.replace("play song","").strip()
        return play_song(song)

    if low.startswith("search song "):
        song = text.replace("search song","").strip()
        return search_song(song)

    if "play music" in low:
        return play_latest_songs()
    return None
def handle_memory_ai(cmd):

    cmd = cmd.lower()

    if "remember that" in cmd:

        data = cmd.replace("remember that","").strip()

        remember(data)

        return "Maine yaad rakh liya."

    if "what do you remember about" in cmd:

        q = cmd.replace("what do you remember about","").strip()

        res = recall(q)

        return "Mujhe yaad hai: " + ", ".join(res)

    return None
# =========================
# LLM ROUTER
# =========================
def get_response(user_input, history):
    low = user_input.lower()
    if "news" in low or "latest" in low:
        return ask_perplexity(user_input)

    if "explain" in low or "why" in low:
        return ask_gemini(user_input)

    # Local Mistral (streamed)
    reply = ""
    for token in generate_stream(user_input, history):
        reply += token
    return reply
def handle_file_commands(cmd):

    if "list files" in cmd:
        return str(list_files())

    if "read file" in cmd:
        name = cmd.replace("read file","").strip()
        return read_file(name)

    if "create folder" in cmd:
        name = cmd.replace("create folder","").strip()
        return create_folder(name)

    return None
def handle_visual_ai(cmd):

    cmd = cmd.lower()

    if "detect objects" in cmd:

        objs = detect_objects()

        if not objs:
            return "Koi object detect nahi hua."

        names = [o["name"] for o in objs]

        return "Screen par ye objects hain: " + ", ".join(names)


    if "click object" in cmd or "click on object" in cmd or "click the object" in cmd:

        target = cmd.replace("click object","").strip()

        objs = detect_objects()

        for o in objs:

            if target in o["name"]:

                auto.move_mouse(o["x"], o["y"])
                auto.click()

                return f"{target} par click kar diya"

        return f"{target} nahi mila"

    return None
def save_target(name, pos):

    with open("vision_memory.json","r") as f:
        data = json.load(f)

    data[name] = pos

    with open("vision_memory.json","w") as f:
        json.dump(data, f)
def play_youtube_video(query):
    search = urllib.parse.quote(query)

    url = f"https://www.youtube.com/results?search_query={search}"
    webbrowser.open(url)

    time.sleep(5)

    # Click first video
    auto.move_mouse(500, 350)
    auto.click()

    print("Playing:", query)

def process_command(command):

    command = command.lower()

    if "play" in command and "youtube" in command:
        song = command.replace("play", "").replace("youtube", "")
        play_youtube_video(song)

    elif "next video" in command:
        next_video()
    elif "read screen" in command:
        print(read_screen_text())
# =========================
# VISUAL AUTONOMOUS AGENT
# =========================

def visual_agent(command):

    cmd = command.lower()

    if "find and click" in cmd:

        target = cmd.replace("find and click", "").strip()

        elements = detect_gui_elements()

        for e in elements:

            if target in str(e).lower():

                auto.move_mouse(e["x"], e["y"])
                auto.click()

                return f"{target} par click kar diya."

        return f"{target} screen par nahi mila."

    if "what do you see" in cmd:

        info = describe_screen()

        return f"Screen par {info['objects_detected']} objects aur {info['windows_detected']} windows hain."

    return None

# =========================
# DESKTOP TASK AGENT
# =========================

def desktop_agent(command):

    steps = plan_task(command)

    if not steps:
        return None

    execute_task_chain(steps)

    return "Task complete kar diya."

def run_autonomous_agent(goal):

    speak_async("Soch rahi hoon...", "thinking")

    handlers = [
        handle_rosy_commands,
        handle_automation_commands,
        handle_screen_commands,
        handle_web_commands,
        handle_visual_ai
    ]

    steps = plan(goal)

    for step in steps:

        try:
            print("➡️ Step:", step)

            result = act(step, handlers)

            if result:
                speak_async(result, "happy")

            observation = observe()

            correction = self_correct(goal, step, observation)

            if "done" in correction.lower():
                speak_async("Task complete 💖", "happy")
                return

            # update goal dynamically
            goal = correction

        except Exception as e:

            err = traceback.format_exc()

            print("❌ Error:", err)

            fix = improve_code(step, err)

            print("🧠 Suggested Fix:\n", fix)

            speak_async("Mujhse error ho gaya... sudhar rahi hoon.", "sad")

    speak_async("Task pura nahi ho paaya...", "thinking")

def act_on_screen(command):

    state = get_state()

    prompt = f"""
You see this screen:

{state}

User command:
{command}

Tell ONE action:
- click x y
- type text
- scroll up/down
- open app

Only give action.
"""

    action = think(command, state)

    print("🧠 Action:", action)

    # --- parse action ---
    try:
        if "click" in action:
            parts = action.split()
            x = int(parts[-2])
            y = int(parts[-1])
            click(x, y)

        elif "type" in action:
            text = action.replace("type", "").strip()
            type_text(text)

        elif "scroll" in action:
            from control.automation import scroll
            if "down" in action:
                scroll(-500)
            else:
                scroll(500)

        return True

    except Exception as e:
        print("Action error:", e)
        return False
def smart_action(command):

    command = command.lower()

    # extract target
    target = command.replace("click", "").replace("open", "").strip()

    pos = find_target(target)

    if pos:
        x, y = pos
        click(x, y)
        return f"Clicked {target}"

    # typing
    if "type" in command:
        text = command.replace("type", "").strip()
        type_text(text)
        return f"Typed {text}"

    return "Could not find target"
# =========================
# MASTER COMMAND ROUTER
# =========================
def whatsapp_callback(data):
    print("📩 New message:", data)
    wa_handler.plugin.start_monitoring(callback=whatsapp_callback)
def handle_rosy_commands(text):

    # screen vision
    result = handle_screen_commands(text)
    if result:
        return result
    if wa_handler:
        try:
            if wa_handler.is_whatsapp_command(text):
                result = wa_handler.handle(text)
            if result:
                return result
        except Exception as e:
            return f"WhatsApp error: {e}"
    # automation
    result = handle_automation_commands(text)
    if result:
        return result

    # music
    result = handle_music_commands(text)
    if result:
        return result

    # web
    result = handle_web_commands(text)
    if result:
        return result

    # file system
    result = handle_file_commands(text)
    if result:
        return result

    # whatsapp
    #result = handle_whatsapp_commands(text)
    #if result:
    #    return result

    # advanced commands
    result = handle_advanced_commands(text)
    if result:
        return result

    return None
#=====================
# MAIN LOOP
# =========================
print("🌹 Rosy idle mode — waiting for wake word…")
while True:
    # 💤 SLEEP MODE
    wait_for_wake_word()

    print("✨ Wake word detected")
    speak_async("Haan jaan ", "happy")
    # 💬 ACTIVE MODE
    while True:
        user_input = listen()
        if not user_input:
            continue

        low = user_input.lower()
        if "how are you" in low:
            speak_async("Main theek hoon… tum kaise ho? ", "happy")
            continue
        if "how r u" in low:
            speak_async("Main theek hoon… tum kaise ho? ", "happy")
            continue
        if "what are you doing" in low:
            speak_async("Bas tumse baat kar rahi hoon… aur kya 💖 ", "happy")
            continue
        if "on screen" in low or "do on screen" in low or "see screen" in low:
            speak_async("Screen dekh rahi hoon...", "thinking")
            act_on_screen(user_input)
            continue
        if "who are you" in low:
            speak_async("Main Rosy hoon… tumhari AI assistant. ", "happy")
            continue
        if "remember that" in user_input.lower():
            parts = user_input.lower().replace("remember that","").split(" is ")
            if len(parts)==2:
                remember(parts[0], parts[1])
                speak_async("Maine yaad rakh liya.", "happy")
                print("You:", user_input)
                continue
        # 🛑 GO BACK TO SLEEP
        if any(x in low for x in ["go to sleep", "bye rosy", "so jao"]):
            speak_async("Theek hai… bula lena 💕", "caring")
            break   # ⬅️ EXIT ACTIVE MODE → back to wake word

        # 🔴 HARD INTERRUPT
        if "stop rosy" in low:
            stop_speaking()
            continue
        if "stop everything" in low:
            stop_vision()
            speak_async("Stopping all actions", "sad")
            continue

        # ⛔ EXIT PROGRAM
        if "exit" in low:
            speak_async("Bye… phir milenge 💖", "caring")
            exit()
        if "play first video" in low or "first video" in low:
            play_first_youtube()
            continue
        if "play next video" in low or "next video" in low:
            youtube_next()
            continue
        if "complete task" in low or "do task" in low:
            goal = user_input.replace("complete task","").replace("do task","").strip()
            run_autonomous_agent(goal)
            continue
        if "click on" in low or "on screen" in low:
            speak_async("Dekh rahi hoon...", "thinking")
            result2 = smart_action(user_input)
            speak_async(result2, "happy")
            continue
        # 🤖 AUTONOMOUS TASK MODE
        TASK_WORDS = [
    "open","close","start","launch",
    "download","install","search","find"
    ]
                      
        if any(low.startswith(x) for x in TASK_WORDS):
            steps = plan_task(user_input)
            if steps:
                execute_task_chain(steps)
                continue
        screen_result = handle_screen_commands(user_input)
        if screen_result:
            speak_async(screen_result, "happy")
            continue
        automation = handle_automation_commands(user_input)
        if automation:
            speak_async(automation, "happy")
            continue
        music = handle_music_commands(user_input)
        if music:
            speak_async(music, "happy")
            continue
        filecommand = handle_file_commands(user_input)
        if filecommand:
            speak_async(filecommand, "happy")
            continue
        # 🖥️ PC CONTROL
        action = handle_command(user_input)
        if action:
            speak_async(action, "caring")
            continue
        # 🌐 WEB CONTROL
        web_action = handle_web_commands(user_input)
        if web_action:
            speak_async(web_action, "happy")
            continue
        auto_task = execute_autonomous_task(user_input)
        if auto_task:
            speak_async(auto_task, "happy")
            continue
        result = handle_advanced_commands(user_input)
        if result:
            speak_async(result, "happy")
            continue
        action = handle_rosy_commands(user_input)
        if action:
            speak_async(action, "happy")
            continue
        vision = visual_agent(user_input)
        if vision:
            speak_async(vision, "happy")
            continue
        task = desktop_agent(user_input)
        if task:
            speak_async(task, "happy")
            continue
        vision = handle_visual_ai(user_input)
        if vision:
            speak_async(vision, "happy")
            continue
        memory1 = handle_memory_ai(user_input)
        if memory1:
            speak_async(memory1, "happy")
            continue
        #wa_result = handle_whatsapp_commands(user_input)
        #if wa_result:
        #    speak_async(wa_result, "happy")
        #    continue
        # 🧠 LLM RESPONSE
        memory.add_user(user_input)
        reply = get_response(user_input, memory.get())
        memory.add_assistant(reply)
        reply = humanize(reply)
        tone = "caring"
        if "!" in reply:
            tone = "happy"
        elif "sorry" in reply.lower():
            tone = "sad"
        elif "wait" in reply.lower():
            tone = "thinking"
        speak_async(reply, tone)
