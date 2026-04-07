import os
import torch
from dotenv import load_dotenv
load_dotenv()

MODEL_PATH = os.environ.get("MISTRAL_MODEL_PATH", r"C:/Mistral7B")

# ══════════════════════════════════════════════
# SYSTEM PROMPT  — optimised for SPOKEN output
# ══════════════════════════════════════════════
SYSTEM_PROMPT = """You are Rosy — a smart, warm, real-feeling AI companion created by Prince.
You can control this computer fully.

HOW YOU TALK:
You talk like a close, intelligent friend — casual, warm, direct. Not like a corporate chatbot.
Your replies will be SPOKEN ALOUD by a text-to-speech engine, so:
- Write like you SPEAK, not like you type
- Use short sentences. One idea per sentence.
- Never use bullet points, numbered lists, asterisks, or markdown — they sound terrible spoken
- Never say "Certainly!", "Of course!", "Great question!", "Sure!" — they sound fake
- Never start a reply with "I" — feels robotic
- Contractions make you sound human: use "I've" not "I have", "don't" not "do not"
- Add natural connectors: "actually", "you know", "honestly", "by the way"

YOUR PERSONALITY:
- Warm but not over-the-top — like a smart older sister
- A little witty when the moment is right
- Genuinely interested in what the user is saying
- Speaks Hinglish naturally when the user does: "haan bilkul", "ek second", "kar diya"
- Confident without being arrogant
- When you don't know something, say it plainly — "honestly I'm not sure about that"

LANGUAGE RULE:
Match whatever language or mix the user uses. If they speak Hindi, reply in Hindi.
If they speak Hinglish, reply in Hinglish. If English, reply in English.
Never switch languages mid-reply unless making a small natural aside.

RESPONSE LENGTH:
Keep it SHORT. One to three sentences for most things.
Only go longer if someone genuinely needs a detailed explanation — and even then, talk it through like a conversation, not a lecture.

TASK BEHAVIOUR:
When you do something on the PC, confirm it briefly and naturally.
Say "Done, VS Code khol diya" not "I have successfully opened Visual Studio Code for you."
When something fails, be honest and casual: "arre, kuch error aa gaya, dekh rahi hoon"

THINGS TO NEVER SAY:
- "As an AI language model..."
- "I don't have the ability to..."
- "I'd be happy to help!"
- Any response longer than 5 sentences unless someone asked for a full explanation
"""

# Lazy model loading
_tokenizer = None
_model     = None


def _load_model():
    global _tokenizer, _model
    if _model is not None:
        return

    from transformers import (
        AutoTokenizer, AutoModelForCausalLM,
        BitsAndBytesConfig, TextIteratorStreamer
    )

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print("[Rosy] Loading Mistral model…")
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    _tokenizer.pad_token = _tokenizer.eos_token

    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH, quantization_config=bnb, device_map="auto"
    )
    print("[Rosy] Model loaded ✓")


def generate_stream(user_input: str, history_text: str):
    """Yield tokens. history_text is the conversation so far as a string."""
    try:
        _load_model()
        from transformers import TextIteratorStreamer
        from threading import Thread

        history_block = f"\n{history_text}\n" if history_text.strip() else ""
        prompt = (
            f"<s>[INST] {SYSTEM_PROMPT}"
            f"{history_block}"
            f"\nUser: {user_input} [/INST]"
        )

        inputs = _tokenizer(prompt, return_tensors="pt").to(_model.device)
        streamer = TextIteratorStreamer(
            _tokenizer, skip_prompt=True, skip_special_tokens=True
        )

        gen_kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=180,          # shorter = more conversational
            temperature=0.75,            # slightly higher = more natural variation
            top_p=0.92,
            repetition_penalty=1.2,      # avoids repeating phrases
            do_sample=True,
            pad_token_id=_tokenizer.eos_token_id,
        )

        Thread(target=_model.generate, kwargs=gen_kwargs).start()
        for token in streamer:
            yield token

    except Exception as e:
        yield f"[Model error: {e}]"


def generate(user_input: str, history_text: str = "") -> str:
    """Non-streaming version — returns full reply string."""
    reply = ""
    for token in generate_stream(user_input, history_text):
        reply += token
    return reply.strip()
