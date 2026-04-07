import re
from whatsapp_rosy import WhatsAppPlugin   # your file from before


# ─────────────────────────────────────────────────────────────
#  COMMAND PARSER
# ─────────────────────────────────────────────────────────────

class WhatsAppCommandHandler:
    """
    Parses natural-language commands and maps them to WhatsApp actions.

    Plug into RosyAI / JarvisAI like this:
        self.wa_cmd = WhatsAppCommandHandler(ai_instance=self)
        self.wa_cmd.start()

    Then in your command router just call:
        response = self.wa_cmd.handle("Send WhatsApp to John saying hey!")
        print(response)   # "✅ WhatsApp sent to John!"
    """

    # ── Trigger words that mean "this is a WhatsApp command" ──
    WHATSAPP_TRIGGERS = [
        "whatsapp", "whats app", "wp", "wapp",
        "send message", "send a message",
        "message to", "msg to",
        "text to", "send text",
    ]

    # ── Separator words between contact and message ────────────
    SEPARATORS = [
        "saying", "that", "with message", "message",
        "with text", "text", ":", "-", "tell them",
        "tell him", "tell her", "write", "saying that",
    ]

    # ── Read/check triggers ────────────────────────────────────
    READ_TRIGGERS = [
        "read", "show", "check", "see", "get",
        "what did", "what has", "latest from",
        "messages from", "chat with",
    ]

    # ── Who messaged triggers ──────────────────────────────────
    WHO_TRIGGERS = [
        "who messaged", "who texted", "who sent", "any messages",
        "new messages", "unread", "who wrote", "any whatsapp",
        "check whatsapp", "any new","kisne message kiya", "kya whatsapp aaya", "kya message aaya", "kya whatsapp aayi", "kya whatsapp aya", "kya message aaya", "kya message aayi", "kya message aya", "kya whatsapp aayi hai", "kya whatsapp aya hai", "kya message aayi hai", "kya message aya hai",
    ]

    def __init__(self, ai_instance=None, headless: bool = True):
        self.plugin = WhatsAppPlugin(ai_instance=ai_instance, headless=headless)
        self._started = False

    def start(self) -> bool:
        """Start the WhatsApp browser session."""
        ok = self.plugin.start()
        self._started = ok
        return ok

    def stop(self):
        self.plugin.stop()
        self._started = False

    # ══════════════════════════════════════════
    #  MAIN ENTRY POINT
    # ══════════════════════════════════════════

    def handle(self, command: str) -> str:
        """
        Pass any voice/text command here.
        Returns a response string Rosy can speak or display.

        Examples:
            handle("Send WhatsApp to John saying Hello!")
            handle("Who messaged me on WhatsApp?")
            handle("Read WhatsApp from Alice")
        """
        if not self._started:
            return "WhatsApp is not connected. Please start the WhatsApp session first."

        cmd = command.lower().strip()

        # ── Route to the right action ──────────────────────────
        if self._is_who_messaged(cmd):
            return self._do_who_messaged()

        if self._is_read_command(cmd):
            contact = self._extract_contact_for_read(cmd)
            if contact:
                return self._do_read(contact)
            return "Who do you want to read messages from?"

        if self._is_send_command(cmd):
            contact, message = self._parse_send_command(command)  # use original case
            if contact and message:
                return self._do_send(contact, message)
            elif contact and not message:
                return f"What message should I send to {contact}?"
            else:
                return "I didn't catch the contact name or message. Try: 'WhatsApp John saying Hello'"

        return None   # not a WhatsApp command — let Rosy handle it normally

    def is_whatsapp_command(self, command: str) -> bool:
        """Quick check — is this command meant for WhatsApp?"""
        cmd = command.lower()
        return any(trigger in cmd for trigger in self.WHATSAPP_TRIGGERS + self.WHO_TRIGGERS)

    # ══════════════════════════════════════════
    #  DETECTION HELPERS
    # ══════════════════════════════════════════

    def _is_send_command(self, cmd: str) -> bool:
        send_words = ["send", "message", "msg", "text", "tell", "write", "whatsapp", "wp"]
        return any(w in cmd for w in send_words)

    def _is_read_command(self, cmd: str) -> bool:
        return any(t in cmd for t in self.READ_TRIGGERS)

    def _is_who_messaged(self, cmd: str) -> bool:
        return any(t in cmd for t in self.WHO_TRIGGERS)

    # ══════════════════════════════════════════
    #  PARSE:  contact + message from command
    # ══════════════════════════════════════════

    def _parse_send_command(self, command: str) -> tuple[str | None, str | None]:
        """
        Extract (contact, message) from a natural-language command.

        Handles patterns like:
          "Send WhatsApp to John saying Hello"
          "Message +919876543210 that I'll be late"
          "WhatsApp Priya - how are you?"
          "Send message to mom: coming home soon"
          "Tell John on WhatsApp that dinner is ready"
          "WhatsApp 9876543210 hey there"
        """
        text = command.strip()

        # ── Pattern 1: explicit "to <contact> <sep> <message>" ──
        # e.g. "send whatsapp to John saying Hello"
        match = re.search(
            r'\bto\s+([+\d\w\s]{2,30?}?)\s+(?:' +
            '|'.join(re.escape(s) for s in self.SEPARATORS) +
            r')\s+(.+)',
            text, re.IGNORECASE
        )
        if match:
            return match.group(1).strip(), match.group(2).strip()

        # ── Pattern 2: "tell <contact> on whatsapp that <message>" ──
        match = re.search(
            r'\btell\s+(\w[\w\s]{0,20}?)\s+(?:on\s+whatsapp\s+)?(?:that|to)\s+(.+)',
            text, re.IGNORECASE
        )
        if match:
            return match.group(1).strip(), match.group(2).strip()

        # ── Pattern 3: "whatsapp/message <contact> - <message>" ──
        # separator is -, :, or just a clear pause word
        match = re.search(
            r'(?:whatsapp|message|msg|text)\s+([+\d\w\s]{2,25?}?)\s*(?:' +
            '|'.join(re.escape(s) for s in self.SEPARATORS + ['-', ':']) +
            r')\s+(.+)',
            text, re.IGNORECASE
        )
        if match:
            return match.group(1).strip(), match.group(2).strip()

        # ── Pattern 4: phone number anywhere + message after separator ──
        phone_match = re.search(r'(\+?\d[\d\s\-]{8,14}\d)', text)
        if phone_match:
            phone = phone_match.group(1).replace(" ", "").replace("-", "")
            # Message is everything after the phone number (strip leading separators)
            after_phone = text[phone_match.end():].strip()
            after_phone = re.sub(
                r'^(?:' + '|'.join(re.escape(s) for s in self.SEPARATORS) + r')\s*',
                '', after_phone, flags=re.IGNORECASE
            ).strip()
            if after_phone:
                return phone, after_phone

        # ── Pattern 5: last resort — split on first separator word ──
        # Remove common lead-in words first
        cleaned = re.sub(
            r'^(?:send\s+)?(?:a\s+)?(?:whatsapp\s+)?(?:message\s+)?(?:to\s+)?',
            '', text, flags=re.IGNORECASE
        ).strip()

        for sep in self.SEPARATORS:
            pattern = re.compile(r'^(.+?)\s+' + re.escape(sep) + r'\s+(.+)$', re.IGNORECASE)
            m = pattern.match(cleaned)
            if m:
                contact = m.group(1).strip()
                msg = m.group(2).strip()
                # Sanity: contact shouldn't be super long
                if len(contact.split()) <= 4:
                    return contact, msg

        return None, None

    def _extract_contact_for_read(self, cmd: str) -> str | None:
        """Extract contact name from a read command."""
        # "read messages from Alice" / "show chat with Bob" / "latest from +91..."
        match = re.search(
            r'(?:from|with|of|by)\s+([+\d\w][\w\s\d+\-]{1,25})',
            cmd, re.IGNORECASE
        )
        if match:
            return match.group(1).strip()

        # "read Alice's messages"
        match = re.search(r"(\w[\w\s]{1,20})'s?\s+(?:messages?|chat|whatsapp)", cmd, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    # ══════════════════════════════════════════
    #  ACTIONS
    # ══════════════════════════════════════════

    def _do_send(self, contact: str, message: str) -> str:
        print(f"[RosyAI] Sending WhatsApp to '{contact}': {message[:60]}")
        # ✅ BUG FIX: Previously had a try/except block AFTER the return statements
        # (dead code that never ran). Now properly handles number vs name routing.
        try:
            if contact.startswith("+") or contact.replace(" ", "").isdigit():
                ok = self.plugin.send(contact, message, by_number=True)
            else:
                ok = self.plugin.send(contact, message, by_number=False)

            if ok:
                return f"✅ WhatsApp sent to {contact}!"
            else:
                return f"❌ Could not send WhatsApp to {contact}. They might not be in your contacts."
        except Exception as e:
            return f"❌ Error sending to {contact}: {e}"
    def _do_read(self, contact: str, count: int = 5) -> str:
        print(f"[RosyAI] Reading WhatsApp from '{contact}'")
        return self.plugin.read_pretty(contact, count)

    def _do_who_messaged(self) -> str:
        print("[RosyAI] Checking unread WhatsApp messages…")
        return self.plugin.who_messaged()


# ─────────────────────────────────────────────────────────────
#  HOW TO ADD THIS TO YOUR ROSYAI / JARVISAI CLASS
# ─────────────────────────────────────────────────────────────
"""
STEP 1 — Import and attach in __init__:

    from whatsapp_command_handler import WhatsAppCommandHandler

    class RosyAI:
        def __init__(self):
            ...
            self.whatsapp = WhatsAppCommandHandler(ai_instance=self)
            self.whatsapp.start()


STEP 2 — Add to your main command router:

    def process_command(self, command: str) -> str:
        # Check WhatsApp first
        if self.whatsapp.is_whatsapp_command(command):
            return self.whatsapp.handle(command)

        # ... rest of your Rosy logic
        elif "play music" in command:
            ...


STEP 3 — That's it! Rosy now understands:

    "Send WhatsApp to John saying I'm on my way"
    "Message +919876543210 that the meeting is at 5"
    "WhatsApp mom - coming home for dinner"
    "Tell Priya on WhatsApp that I'll call her later"
    "Who messaged me on WhatsApp?"
    "Read WhatsApp from Alice"
    "Check my unread WhatsApp messages"
"""


# ─────────────────────────────────────────────────────────────
#  QUICK TEST  (run directly to verify parsing without browser)
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from whatsapp_command_handler import WhatsAppCommandHandler

    # Test parser only (no browser needed)
    handler = WhatsAppCommandHandler.__new__(WhatsAppCommandHandler)
    handler._started = True   # skip browser for test

    test_commands = [
        "Send WhatsApp to John saying Hello there!",
        "Message +919876543210 that I'll be late",
        "WhatsApp Priya - how are you doing?",
        "Send message to mom: coming home soon",
        "Tell Alice on WhatsApp that dinner is ready",
        "whatsapp 9876543210 hey what's up",
        "Message Bob saying good morning have a nice day",
        "Who messaged me on WhatsApp?",
        "Read WhatsApp from Alice",
        "Check my unread WhatsApp messages",
    ]

    print("=" * 60)
    print("  PARSING TEST — No browser needed")
    print("=" * 60)

    for cmd in test_commands:
        print(f"\n🎙 Command : {cmd}")

        if handler._is_who_messaged(cmd.lower()):
            print(f"   Action  : WHO_MESSAGED")
        elif handler._is_read_command(cmd.lower()):
            contact = handler._extract_contact_for_read(cmd.lower())
            print(f"   Action  : READ  →  contact='{contact}'")
        elif handler._is_send_command(cmd.lower()):
            contact, message = handler._parse_send_command(cmd)
            print(f"   Action  : SEND  →  contact='{contact}'  |  message='{message}'")
        else:
            print(f"   Action  : (not a WhatsApp command)")