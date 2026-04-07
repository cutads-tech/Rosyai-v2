import re
import time

# ── LLM backend ───────────────────────────────
try:
    from external_llm import ask_gemini
    GEMINI_OK = True
except Exception:
    GEMINI_OK = False

try:
    from llm_mistral import generate as mistral_generate
    MISTRAL_OK = True
except Exception:
    MISTRAL_OK = False

# ── Automation ────────────────────────────────
try:
    from control import automation as auto
    AUTO_OK = True
except Exception:
    AUTO_OK = False

try:
    import pyautogui
    PYAUTOGUI_OK = True
except Exception:
    PYAUTOGUI_OK = False


# ══════════════════════════════════════════════
# CONTENT TYPE DEFINITIONS
# ══════════════════════════════════════════════
CONTENT_TYPES = {
    # Essays & Articles
    "essay":        "Write a well-structured essay with introduction, body paragraphs, and conclusion.",
    "article":      "Write an informative article with clear sections and subheadings.",
    "blog":         "Write an engaging blog post with a catchy intro, main points, and conclusion.",
    "blog post":    "Write an engaging blog post with a catchy intro, main points, and conclusion.",
    "report":       "Write a formal report with executive summary, findings, and recommendations.",

    # Creative Writing
    "poem":         "Write a beautiful, creative poem with rhythm and imagery.",
    "poetry":       "Write a beautiful, creative poem with rhythm and imagery.",
    "story":        "Write a short creative story with characters, plot, and a satisfying ending.",
    "short story":  "Write a short creative story with engaging characters and plot.",
    "letter":       "Write a formal and professional letter with proper salutation and closing.",
    "application":  "Write a formal application letter.",

    # Professional
    "email":        "Write a clear, professional email with subject, greeting, body, and closing.",
    "cover letter": "Write a compelling cover letter highlighting relevant skills and experience.",
    "resume":       "Write a clean, professional resume template with all standard sections.",
    "cv":           "Write a comprehensive CV template with all standard sections.",
    "proposal":     "Write a structured business proposal with objectives, plan, and budget sections.",
    "summary":      "Write a concise executive summary covering all key points.",
    "plan":         "Write a detailed action plan with steps, timelines, and goals.",

    # Technical / Code
    "code":         "Write clean, well-commented, working code.",
    "python code":  "Write clean, well-commented Python code with proper functions.",
    "script":       "Write a complete, working script with error handling.",
    "function":     "Write a clean, well-documented function with docstring.",
    "program":      "Write a complete program with main function and proper structure.",
    "algorithm":    "Write a clear algorithm with step-by-step explanation and code.",
    "html":         "Write well-structured HTML code with proper tags and comments.",
    "css":          "Write clean CSS with proper selectors and comments.",

    # Notes & Lists
    "notes":        "Write clear, organized notes with bullet points and headings.",
    "note":         "Write clear, organized notes with bullet points and headings.",
    "to-do list":   "Write a practical, organized to-do list with priorities.",
    "todo list":    "Write a practical, organized to-do list with priorities.",
    "checklist":    "Write a detailed checklist with all necessary items.",
    "list":         "Write a well-organized list with clear items.",
    "outline":      "Write a detailed outline with main points and subpoints.",

    # Educational
    "assignment":   "Write a thorough academic assignment with proper structure and references.",
    "homework":     "Write a complete homework solution with clear explanations.",
    "speech":       "Write an engaging speech with strong opening, body, and memorable closing.",
    "presentation": "Write detailed presentation notes with slide-by-slide points.",
    "definition":   "Write a clear, thorough definition with examples.",
    "explanation":  "Write a clear, detailed explanation suitable for the topic.",

    # Messages
    "message":      "Write a warm, personal message appropriate for the context.",
    "reply":        "Write a thoughtful, appropriate reply.",
    "apology":      "Write a sincere, heartfelt apology letter.",
    "invitation":   "Write a warm and clear invitation with all necessary details.",
    "announcement": "Write a clear and engaging announcement.",
    "description":  "Write a vivid, detailed description.",
    "review":       "Write a balanced, insightful review with pros and cons.",
    "bio":          "Write a professional biography with key highlights.",
    "biography":    "Write a comprehensive biography covering life events and achievements.",
}

# App name → how to open it (maps to pc_control keys)
APP_OPEN_COMMANDS = {
    "notepad":       "open notepad",
    "note pad":      "open notepad",
    "vs code":       "open vscode",
    "vscode":        "open vscode",
    "visual studio": "open vscode",
    "word":          "open word",
    "ms word":       "open word",
    "microsoft word":"open word",
    "wordpad":       "open wordpad",
    "excel":         "open excel",
    "gedit":         "open gedit",
    "sublime":       "open sublime",
    "atom":          "open atom",
}

# Apps where we wait longer before typing (heavier apps)
APP_WAIT_TIMES = {
    "word":   4.0,
    "excel":  4.0,
    "vscode": 3.5,
    "vs code":3.5,
    "notepad":1.5,
    "wordpad":2.5,
}


# ══════════════════════════════════════════════
# INTENT PARSER
# ══════════════════════════════════════════════
def parse_write_intent(text: str) -> dict | None:
    """
    Parse a natural language write command into structured intent.

    Returns dict with keys:
        content_type  — e.g. "essay", "poem", "code"
        topic         — e.g. "climate change", "sort a list"
        app           — e.g. "notepad", "vs code", or None
        raw           — original text
    Returns None if not a write command.
    """
    t = text.lower().strip()

    # Must start with a write-like trigger
    WRITE_TRIGGERS = (
        "write", "compose", "create", "make", "generate",
        "draft", "type", "produce", "prepare", "likh",
        "likho", "bana", "banao"
    )
    if not any(t.startswith(w) for w in WRITE_TRIGGERS):
        return None

    # ── Detect target app ─────────────────────
    detected_app = None
    app_pattern = r"\b(?:in|on|using|use|inside|open)\s+(" + "|".join(
        re.escape(a) for a in sorted(APP_OPEN_COMMANDS.keys(), key=len, reverse=True)
    ) + r")\b"
    app_match = re.search(app_pattern, t, re.I)
    if app_match:
        detected_app = app_match.group(1).strip()
        # Remove the app phrase from text for cleaner parsing
        t_clean = re.sub(app_pattern, "", t, flags=re.I).strip()
    else:
        t_clean = t

    # ── Detect content type ───────────────────
    detected_type = None
    detected_type_key = None

    # Sort by length descending so "blog post" matches before "post"
    for ctype in sorted(CONTENT_TYPES.keys(), key=len, reverse=True):
        if ctype in t_clean:
            detected_type = ctype
            detected_type_key = ctype
            break

    if detected_type is None:
        return None     # not a recognisable write command

    # ── Extract topic ─────────────────────────
    # Remove trigger word + content type → what's left is the topic
    topic = t_clean
    for trigger in WRITE_TRIGGERS:
        topic = re.sub(rf"^{trigger}\s+(a\s+|an\s+|the\s+)?", "", topic, flags=re.I)

    topic = re.sub(re.escape(detected_type), "", topic, flags=re.I)

    # Remove filler words
    topic = re.sub(
        r"\b(about|on|regarding|for|related to|of|titled|titled as|named|"
        r"ke baare mein|par|ke liye|mein)\b",
        " ", topic, flags=re.I
    )
    topic = re.sub(r"\s+", " ", topic).strip(" .,!?-")

    return {
        "content_type": detected_type_key,
        "topic":        topic if topic else None,
        "app":          detected_app,
        "raw":          text,
    }


# ══════════════════════════════════════════════
# CONTENT GENERATOR  (uses best available LLM)
# ══════════════════════════════════════════════
def generate_content(content_type: str, topic: str | None) -> str:
    """
    Generate actual content for the given type and topic using LLM.
    Returns the generated text string.
    """
    instruction = CONTENT_TYPES.get(content_type, "Write content about the following topic.")
    topic_str   = topic if topic else content_type

    # ── Build a precise, content-focused prompt ──
    is_code = any(w in content_type for w in ("code", "script", "function", "program", "html", "css", "algorithm"))

    if is_code:
        prompt = f"""Write {content_type} for the following task: {topic_str}

Requirements:
- Write ONLY the code, no extra explanation before it
- Add brief comments explaining key parts
- Make it complete and working
- Use proper indentation

Code:"""
    else:
        prompt = f"""{instruction}

Topic: {topic_str}

Requirements:
- Write the FULL content, not a summary or outline
- Make it detailed, well-structured, and high quality
- Minimum 200 words unless it's a short-form type (poem, message, list)
- Use proper formatting with paragraphs
- Do NOT include meta-commentary like "Here is your essay:" — start directly
- Do NOT say "I'll write" or "Sure!" — just write the content immediately

Begin writing now:"""

    # Try Gemini first (better quality for long-form content)
    if GEMINI_OK:
        try:
            result = ask_gemini(prompt)
            if result and len(result.strip()) > 50:
                return result.strip()
        except Exception as e:
            print(f"[command_parser] Gemini error: {e}")

    # Fallback to local Mistral
    if MISTRAL_OK:
        try:
            result = mistral_generate(prompt, "")
            if result and len(result.strip()) > 30:
                return result.strip()
        except Exception as e:
            print(f"[command_parser] Mistral error: {e}")

    # Last resort: return a placeholder so user knows what happened
    return f"[Content generation failed — no LLM available]\n\nRequested: {content_type} about {topic_str}"


# ══════════════════════════════════════════════
# APP OPENER
# ══════════════════════════════════════════════
def open_app_for_writing(app_name: str) -> float:
    """
    Open the target app and return how many seconds to wait for it to load.
    """
    if app_name is None:
        return 0.0

    # Resolve to pc_control command
    app_key = app_name.lower().strip()
    open_cmd = APP_OPEN_COMMANDS.get(app_key)
    if open_cmd is None:
        return 0.0

    wait = APP_WAIT_TIMES.get(app_key, 2.0)

    try:
        from pc_control import handle_command
        handle_command(open_cmd)
        print(f"[command_parser] Opened '{app_name}', waiting {wait}s…")
        time.sleep(wait)
    except Exception as e:
        print(f"[command_parser] App open error: {e}")

    return wait


# ══════════════════════════════════════════════
# SMART TYPER
# ══════════════════════════════════════════════
def type_content_smart(content: str):
    """
    Type content into the focused window.
    Uses clipboard paste for speed and reliability (avoids char-by-char issues with special chars).
    Falls back to pyautogui.write() if clipboard is unavailable.
    """
    if not content:
        return

    # Method 1: clipboard paste (fastest, handles all characters)
    try:
        import pyperclip
        pyperclip.copy(content)
        time.sleep(0.2)
        if AUTO_OK:
            auto.hotkey("ctrl", "v")
        elif PYAUTOGUI_OK:
            pyautogui.hotkey("ctrl", "v")
        print(f"[command_parser] Pasted {len(content)} chars via clipboard ✅")
        return
    except Exception as e:
        print(f"[command_parser] Clipboard paste failed: {e} — trying write()")

    # Method 2: pyautogui write (slower but works without pyperclip)
    try:
        if AUTO_OK:
            auto.type_text(content)
        elif PYAUTOGUI_OK:
            # chunk to avoid dropped chars on long strings
            CHUNK = 200
            for i in range(0, len(content), CHUNK):
                pyautogui.write(content[i:i+CHUNK], interval=0.01)
                time.sleep(0.05)
        print(f"[command_parser] Typed {len(content)} chars ✅")
    except Exception as e:
        print(f"[command_parser] Type error: {e}")


# ══════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════
def handle_smart_write(text: str) -> str | None:
    """
    Full pipeline: parse → generate → open app → type.
    Returns a status string for Rosy to speak, or None if not a write command.
    """
    intent = parse_write_intent(text)
    if intent is None:
        return None

    content_type = intent["content_type"]
    topic        = intent["topic"]
    app          = intent["app"]
    topic_str    = topic if topic else content_type

    print(f"[command_parser] Intent → type='{content_type}', topic='{topic}', app='{app}'")

    # Step 1: Tell user we're generating
    status_msg = f"{content_type.title()} generate kar rahi hoon"
    if topic:
        status_msg += f" '{topic}' par"
    status_msg += "… ek second 📝"

    # Step 2: Generate content
    print(f"[command_parser] Generating {content_type} about '{topic_str}'…")
    content = generate_content(content_type, topic)
    print(f"[command_parser] Generated {len(content)} chars")

    # Step 3: Open app if specified
    if app:
        open_app_for_writing(app)
        # Click into the text area after app opens
        try:
            if PYAUTOGUI_OK:
                # Click centre of screen to focus text area
                screen_w, screen_h = pyautogui.size()
                pyautogui.click(screen_w // 2, screen_h // 2)
                time.sleep(0.3)
        except Exception:
            pass

    # Step 4: Type the content
    type_content_smart(content)

    # Step 5: Return spoken confirmation
    word_count = len(content.split())
    confirm = f"{content_type.title()} likh diya"
    if topic:
        confirm += f" '{topic_str}' par"
    confirm += f" — {word_count} words ✅"
    return confirm


# ══════════════════════════════════════════════
# QUICK TEST  (run this file directly to test)
# ══════════════════════════════════════════════
if __name__ == "__main__":
    test_commands = [
        "write essay on climate change on notepad",
        "write a poem about love",
        "write Python code to sort a list",
        "compose an email about project update",
        "make a to-do list for Monday",
        "write a short story about a robot in VS Code",
        "create a cover letter for software engineer job",
        "write notes on machine learning",
        "generate a resume template",
        "write code for binary search",
        "write essay about artificial intelligence",
        "write hello world program on notepad",
    ]

    print("=" * 60)
    print("COMMAND PARSER TEST")
    print("=" * 60)
    for cmd in test_commands:
        result = parse_write_intent(cmd)
        print(f"\n  Input : '{cmd}'")
        if result:
            print(f"  Type  : {result['content_type']}")
            print(f"  Topic : {result['topic']}")
            print(f"  App   : {result['app']}")
        else:
            print(f"  → Not a write command")
    print("\n" + "=" * 60)
