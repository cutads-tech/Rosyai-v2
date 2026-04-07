import traceback

try:
    from vision_yolo import detect_objects
    from screen_vision import describe_screen
except ImportError:
    def detect_objects(): return []
    def describe_screen(): return {}

from task_planner import plan_task
from llm_mistral import generate_stream


# ─────────────────────────────────────────────
# OBSERVE — capture current state
# ─────────────────────────────────────────────
def observe() -> dict:
    try:
        screen = describe_screen()
        objects = detect_objects()
        return {
            "windows": screen.get("windows_detected", 0),
            "objects": screen.get("objects_detected", 0),
            "text": screen.get("visible_text", "")[:300],
            "detected_items": [o["name"] for o in objects[:10]],
        }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
# THINK — LLM decides next action
# ─────────────────────────────────────────────
def think(goal: str, observation: dict = None) -> str:
    obs_text = str(observation) if observation else "No observation available"
    prompt = f"""You are an autonomous AI agent.

GOAL: {goal}

CURRENT SCREEN STATE:
{obs_text}

Give ONE short action command. Examples:
- click 500 350
- type Hello World
- scroll down
- open chrome
- search youtube lofi music
- speak Done

Only give the action. No explanation."""

    reply = ""
    for t in generate_stream(prompt, ""):
        reply += t
    return reply.strip()


# ─────────────────────────────────────────────
# PLAN — break goal into steps
# ─────────────────────────────────────────────
def plan(goal: str) -> list:
    """Return list of step strings to achieve the goal."""
    # Try task_planner first
    steps = plan_task(goal)
    if steps:
        return [f"{action} {data or ''}" for action, data in steps]

    # Fallback: LLM-based planning
    prompt = f"""Break this goal into 3–5 short steps:
GOAL: {goal}

Format:
1. step one
2. step two
3. step three

Only steps. No explanation."""

    reply = ""
    for t in generate_stream(prompt, ""):
        reply += t

    lines = [l.strip() for l in reply.strip().splitlines() if l.strip()]
    steps_out = []
    for line in lines:
        # strip leading numbers/bullets
        clean = line.lstrip("0123456789.-) ").strip()
        if clean:
            steps_out.append(clean)

    return steps_out if steps_out else [goal]


# ─────────────────────────────────────────────
# ACT — run handlers for a step
# ─────────────────────────────────────────────
def act(step: str, handlers: list):
    for h in handlers:
        try:
            result = h(step)
            if result:
                return result
        except Exception:
            continue
    return None


# ─────────────────────────────────────────────
# SELF CORRECT — evaluate and adjust
# ─────────────────────────────────────────────
def self_correct(goal: str, last_step: str, observation: dict) -> str:
    prompt = f"""GOAL: {goal}

LAST ACTION: {last_step}

NEW SCREEN STATE: {str(observation)[:300]}

Is the goal completed? If yes, say exactly: DONE
If not, give the next best action (one line)."""

    reply = ""
    for t in generate_stream(prompt, ""):
        reply += t
    return reply.strip()


# ─────────────────────────────────────────────
# IMPROVE CODE — suggest fix for errors
# ─────────────────────────────────────────────
def improve_code(code: str, error: str) -> str:
    prompt = f"""Fix this Python code.

CODE:
{code}

ERROR:
{error}

Return ONLY the corrected code. No explanation."""

    reply = ""
    for t in generate_stream(prompt, ""):
        reply += t
    return reply.strip()
