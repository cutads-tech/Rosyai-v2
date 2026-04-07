class Memory:
    def __init__(self, max_turns: int = 12):
        self.history = []
        self.max_turns = max_turns

    def add_user(self, text: str):
        self.history.append({"role": "user", "content": text})
        if len(self.history) > self.max_turns * 2:
            # Keep last max_turns * 2 messages
            self.history = self.history[-(self.max_turns * 2):]

    def add_assistant(self, text: str):
        self.history.append({"role": "assistant", "content": text})
        if len(self.history) > self.max_turns * 2:
            self.history = self.history[-(self.max_turns * 2):]

    def get(self) -> str:
        """Return conversation history as a formatted string for LLM."""
        lines = []
        for msg in self.history:
            role = "User" if msg["role"] == "user" else "Rosy"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def get_messages(self) -> list:
        """Return history as list of dicts (for OpenAI-style APIs)."""
        return list(self.history)

    def clear(self):
        self.history.clear()

    def last_user(self) -> str:
        for msg in reversed(self.history):
            if msg["role"] == "user":
                return msg["content"]
        return ""
