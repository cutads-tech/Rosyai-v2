import re


# Mapping: keyword → (action, data_extractor)
RULES = [
    # YouTube
    (r"youtube.*search (.+)", "search_youtube", lambda m: m.group(1).strip()),
    (r"search (.+) on youtube",  "search_youtube", lambda m: m.group(1).strip()),
    (r"play (.+) on youtube",    "search_youtube", lambda m: m.group(1).strip()),
    (r"\bopen youtube\b",        "open_youtube",  lambda m: None),

    # Google
    (r"search (.+) on google",   "search_google", lambda m: m.group(1).strip()),
    (r"google (.+)",             "search_google", lambda m: m.group(1).strip()),
    (r"\bopen google\b",         "search_google", lambda m: ""),

    # Scroll
    (r"scroll down",  "scroll_down", lambda m: None),
    (r"scroll up",    "scroll_up",   lambda m: None),

    # Speak
    (r"say (.+)",    "speak", lambda m: m.group(1).strip()),
    (r"tell me (.+)","speak", lambda m: m.group(1).strip()),

    # Wait
    (r"wait (\d+) seconds?", "wait", lambda m: m.group(1)),
]


def plan_task(user_input: str) -> list:
    """
    Returns list of (action, data) tuples.
    Tries rule-based matching first, returns empty if no match
    (caller can fall back to LLM planning).
    """
    text = user_input.lower().strip()
    steps = []

    for pattern, action, extractor in RULES:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                data = extractor(m)
            except Exception:
                data = None
            steps.append((action, data))

    # Compound: "open youtube and search X"
    if not steps:
        m = re.search(r"open youtube.*?(?:and|then).*?search (.+)", text)
        if m:
            steps = [("open_youtube", None), ("search_youtube", m.group(1).strip())]

    return steps
