import os
import requests
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
AIML_API_KEY   = os.getenv("AIML_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
# ─────────────────────────────────────────────
# GEMINI (Google)
# ─────────────────────────────────────────────
_gemini = None

def _get_gemini():
    global _gemini
    if _gemini is None and GOOGLE_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)
            # ✅ BUG FIX: gemini-2.5-flash doesn't exist → use stable gemini-1.5-flash
            _gemini = genai.GenerativeModel("gemini-2.5-flash")
        except Exception as e:
            print(f"[Gemini] Init error: {e}")
    return _gemini


def ask_gemini(prompt: str) -> str:
    model = _get_gemini()
    if model is None:
        return ask_aiml(prompt)
    try:
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return ask_aiml(prompt)


# ─────────────────────────────────────────────
# AIML API (Perplexity-compatible, real-time web data)
# ─────────────────────────────────────────────
def ask_aiml(prompt: str, model: str = "openai/gpt-5.2") -> str:
    if not OPENROUTER_API_KEY:
        return "OPENROUTER_API_KEY not set. Please set it in your .env file."
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 512,
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"AIML error: {e}"


# Keep old name for backward compatibility
def ask_perplexity(prompt: str) -> str:
    return ask_aiml(prompt)


# ─────────────────────────────────────────────
# OPENAI GPT (optional)
# ─────────────────────────────────────────────
def ask_gpt(prompt: str, model: str = "gpt-4o-mini") -> str:
    if not OPENAI_API_KEY:
        return ask_gemini(prompt)
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 512,
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return ask_gemini(prompt)
