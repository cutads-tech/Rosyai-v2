import time
import os
import json
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException
)

# ─────────────────────────────────────────────
#  CONFIG  (edit these paths for your machine)
# ─────────────────────────────────────────────
EDGE_DRIVER_PATH = r"D:\rosyai\msedgedriver.exe"
PROFILE_DIR = os.path.expandvars(
    r"C:\Users\%USERNAME%\AppData\Local\Microsoft\Edge\User Data\rosy_whatsapp_profile"
)
# How often (seconds) the background monitor checks for new messages
MONITOR_INTERVAL = 5


# ─────────────────────────────────────────────
#  CORE CLASS
# ─────────────────────────────────────────────

class WhatsAppRosy:
    """
    Full WhatsApp controller for RosyAI / JarvisAI.

    Quick-start:
        wa = WhatsAppRosy()
        wa.start()

        # Send a message
        wa.send_by_number("+919876543210", "Hello!")
        wa.send_by_name("John", "Hey John!")

        # Read messages
        msgs = wa.get_latest_messages("John", count=5)
        inbox = wa.get_unread_chats()

        # Monitor in background — Rosy/Jarvis get a callback
        wa.start_monitoring(callback=my_ai_handler)

        wa.close()
    """

    def __init__(self):
        self.driver = None
        self._monitor_thread = None
        self._monitoring = False
        self._seen_messages: dict[str, set] = {}   # contact → set of msg-ids seen

    # ══════════════════════════════════════════
    #  BROWSER LIFECYCLE
    # ══════════════════════════════════════════

    def start(self, headless: bool = True) -> bool:
        """Launch Edge and open WhatsApp Web."""
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(f"--user-data-dir={PROFILE_DIR}")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")

        try:
            service = Service(EDGE_DRIVER_PATH)
            self.driver = webdriver.Edge(service=service, options=options)
            self.driver.get("https://web.whatsapp.com")
            print("[WhatsApp] Waiting for WhatsApp to load…")
            # Wait until chat list appears (means QR already scanned / session alive)
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@aria-label='Chat list']")
                )
            )
            print("[WhatsApp] ✅ Ready!")
            return True
        except TimeoutException:
            print("[WhatsApp] ❌ QR scan required — open Edge manually, scan QR, then retry.")
            return False
        except Exception as e:
            print(f"[WhatsApp] ❌ Start failed: {e}")
            return False

    def close(self):
        """Stop monitoring and close browser."""
        self.stop_monitoring()
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("[WhatsApp] Browser closed.")

    # ══════════════════════════════════════════
    #  SEND MESSAGES
    # ══════════════════════════════════════════

    def send_by_number(self, phone: str, message: str) -> bool:
        """Send a message using a phone number (include country code, e.g. +91…)."""
        try:
            print(f"[WhatsApp] Sending to {phone}…")
            url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"
            self.driver.get(url)
            time.sleep(5)
            return self._click_send()
        except Exception as e:
            print(f"[WhatsApp] send_by_number error: {e}")
            return False

    def send_by_name(self, contact_name: str, message: str) -> bool:
        """Send a message by searching for a contact name."""
        try:
            print(f"[WhatsApp] Sending to '{contact_name}'…")
            if not self._open_chat_by_name(contact_name):
                return False
            return self._type_and_send(message)
        except Exception as e:
            print(f"[WhatsApp] send_by_name error: {e}")
            return False

    def send_multiple(self, contacts: list[tuple], by_number: bool = True) -> int:
        """
        Send to many contacts.
        contacts = [("name_or_phone", "message"), …]
        Returns count of successful sends.
        """
        success = 0
        for i, (contact, message) in enumerate(contacts, 1):
            print(f"[WhatsApp] [{i}/{len(contacts)}] Sending…")
            if by_number:
                ok = self.send_by_number(contact, message)
            else:
                ok = self.send_by_name(contact, message)
            if ok:
                success += 1
            if i < len(contacts):
                time.sleep(10)   # polite delay between sends
        print(f"[WhatsApp] Sent {success}/{len(contacts)}")
        return success

    # ══════════════════════════════════════════
    #  READ MESSAGES
    # ══════════════════════════════════════════

    def get_latest_messages(self, contact_name: str, count: int = 10) -> list[dict]:
        """
        Open a chat and return the last `count` messages.

        Returns a list of dicts:
            {
                "sender":    "them" | "me",
                "text":      "…",
                "time":      "10:35 AM",
                "timestamp": datetime-or-None
            }
        """
        try:
            if not self._open_chat_by_name(contact_name):
                return []

            time.sleep(2)
            messages = self._scrape_messages(count)
            print(f"[WhatsApp] Got {len(messages)} messages from '{contact_name}'")
            return messages
        except Exception as e:
            print(f"[WhatsApp] get_latest_messages error: {e}")
            return []

    def get_last_message(self, contact_name: str) -> dict | None:
        """
        Get only the single most recent message from a contact.
        Useful for Rosy/Jarvis to quickly check what someone just said.
        """
        msgs = self.get_latest_messages(contact_name, count=1)
        return msgs[-1] if msgs else None

    def get_unread_chats(self) -> list[dict]:
        """
        Scan the chat list and return contacts with unread messages.

        Returns:
            [{"name": "Alice", "unread_count": 3}, …]
        """
        try:
            self.driver.get("https://web.whatsapp.com")
            time.sleep(3)

            unread = []
            # Unread badge spans
            badges = self.driver.find_elements(
                By.XPATH,
                "//span[@aria-label and contains(@class,'unread')]"
            )

            # Broader approach: find chat rows with unread count
            chat_rows = self.driver.find_elements(
                By.XPATH,
                "//div[@role='listitem']"
            )

            for row in chat_rows:
                try:
                    # Contact name
                    name_el = row.find_element(
                        By.XPATH, ".//span[@dir='auto' and @title]"
                    )
                    name = name_el.get_attribute("title")

                    # Unread badge
                    try:
                        badge = row.find_element(
                            By.XPATH, ".//span[@aria-label]"
                        )
                        badge_text = badge.text.strip()
                        if badge_text.isdigit():
                            unread.append({
                                "name": name,
                                "unread_count": int(badge_text)
                            })
                    except NoSuchElementException:
                        pass
                except (NoSuchElementException, StaleElementReferenceException):
                    pass

            print(f"[WhatsApp] Found {len(unread)} unread chat(s)")
            return unread

        except Exception as e:
            print(f"[WhatsApp] get_unread_chats error: {e}")
            return []

    def get_recent_contacts(self, limit: int = 10) -> list[str]:
        """Return the names of the most recently active contacts."""
        try:
            self.driver.get("https://web.whatsapp.com")
            time.sleep(3)

            names = []
            rows = self.driver.find_elements(
                By.XPATH, "//div[@role='listitem']//span[@dir='auto'][@title]"
            )
            for el in rows[:limit]:
                title = el.get_attribute("title")
                if title and title not in names:
                    names.append(title)
            return names
        except Exception as e:
            print(f"[WhatsApp] get_recent_contacts error: {e}")
            return []

    def get_full_chat_history(self, contact_name: str, scroll_times: int = 5) -> list[dict]:
        """
        Scroll up to load older messages and return full visible history.
        `scroll_times` controls how far back to go (each scroll ~20 messages).
        """
        try:
            if not self._open_chat_by_name(contact_name):
                return []

            time.sleep(2)
            chat_area = self.driver.find_element(
                By.XPATH, "//div[@role='application']"
            )

            for _ in range(scroll_times):
                self.driver.execute_script(
                    "arguments[0].scrollTop = 0;", chat_area
                )
                time.sleep(1.5)

            messages = self._scrape_messages(count=999)
            print(f"[WhatsApp] Full history: {len(messages)} messages")
            return messages
        except Exception as e:
            print(f"[WhatsApp] get_full_chat_history error: {e}")
            return []

    # ══════════════════════════════════════════
    #  BACKGROUND MONITOR  (for RosyAI / Jarvis)
    # ══════════════════════════════════════════

    def start_monitoring(self, callback, contacts: list[str] | None = None):
        """
        Start a background thread that watches for new WhatsApp messages
        and calls `callback(event)` when one arrives.

        callback receives a dict:
            {
                "contact":   "Alice",
                "sender":    "them" | "me",
                "text":      "Hey Rosy!",
                "time":      "10:35 AM",
                "timestamp": datetime-or-None
            }

        contacts: list of names to watch. None = watch all unread chats.

        Example integration with RosyAI:
            def rosy_handler(event):
                reply = rosy.think(f"{event['contact']} says: {event['text']}")
                wa.send_by_name(event['contact'], reply)

            wa.start_monitoring(callback=rosy_handler)
        """
        if self._monitoring:
            print("[WhatsApp] Monitor already running.")
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(callback, contacts),
            daemon=True
        )
        self._monitor_thread.start()
        print("[WhatsApp] 🔍 Background monitor started.")

    def stop_monitoring(self):
        """Stop the background monitor thread."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10)
            self._monitor_thread = None
            print("[WhatsApp] Monitor stopped.")

    def _monitor_loop(self, callback, contacts):
        """Internal loop — runs in background thread."""
        print(f"[WhatsApp] Monitor loop active (interval={MONITOR_INTERVAL}s)")
        while self._monitoring:
            try:
                # Figure out which contacts to check
                if contacts:
                    targets = contacts
                else:
                    unread = self.get_unread_chats()
                    targets = [c["name"] for c in unread]

                for contact in targets:
                    msgs = self.get_latest_messages(contact, count=5)
                    for msg in msgs:
                        # Build a unique ID for dedup
                        uid = f"{msg['time']}|{msg['sender']}|{msg['text']}"
                        if contact not in self._seen_messages:
                            self._seen_messages[contact] = set()

                        if uid not in self._seen_messages[contact]:
                            self._seen_messages[contact].add(uid)
                            # Only trigger callback for INCOMING messages
                            if msg["sender"] == "them":
                                event = {**msg, "contact": contact}
                                print(f"[WhatsApp] 📩 New message from {contact}: {msg['text'][:60]}")
                                try:
                                    callback(event)
                                except Exception as cb_err:
                                    print(f"[WhatsApp] Callback error: {cb_err}")

            except Exception as loop_err:
                print(f"[WhatsApp] Monitor loop error: {loop_err}")

            time.sleep(MONITOR_INTERVAL)

    # ══════════════════════════════════════════
    #  HELPER / PRIVATE METHODS
    # ══════════════════════════════════════════

    def _open_chat_by_name(self, contact_name: str) -> bool:
        """Search for and open a contact's chat."""
        try:
            self.driver.get("https://web.whatsapp.com")
            time.sleep(3)

            search_box = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@contenteditable='true'][@title='Search input textbox']")
                )
            )
            search_box.click()
            time.sleep(0.5)
            search_box.clear()
            search_box.send_keys(contact_name)
            time.sleep(2)

            contact = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//span[@title='{contact_name}']")
                )
            )
            contact.click()
            time.sleep(2)
            return True
        except TimeoutException:
            print(f"[WhatsApp] Contact '{contact_name}' not found in search.")
            return False

    def _scrape_messages(self, count: int = 10) -> list[dict]:
        """Scrape visible messages from the currently open chat."""
        messages = []
        try:
            # All message bubbles
            msg_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'message-in') or contains(@class,'message-out')]"
            )

            # Take the last `count` elements
            for el in msg_elements[-count:]:
                try:
                    # Direction
                    classes = el.get_attribute("class") or ""
                    if "message-in" in classes:
                        sender = "them"
                    elif "message-out" in classes:
                        sender = "me"
                    else:
                        continue

                    # Text content
                    try:
                        text_el = el.find_element(
                            By.XPATH,
                            ".//span[@class='selectable-text copyable-text']"
                        )
                        text = text_el.text.strip()
                    except NoSuchElementException:
                        text = "[media/attachment]"

                    # Timestamp
                    time_str = ""
                    timestamp = None
                    try:
                        time_el = el.find_element(
                            By.XPATH, ".//div[@data-pre-plain-text]"
                        )
                        meta = time_el.get_attribute("data-pre-plain-text") or ""
                        # meta looks like: "[10:35 AM, 12/6/2025] Alice: "
                        if meta:
                            bracket_content = meta.split("]")[0].lstrip("[")
                            time_str = bracket_content.split(",")[0].strip()
                    except NoSuchElementException:
                        try:
                            time_el = el.find_element(
                                By.XPATH, ".//span[@data-testid='msg-meta']//span"
                            )
                            time_str = time_el.text.strip()
                        except NoSuchElementException:
                            pass

                    if text:
                        messages.append({
                            "sender": sender,
                            "text": text,
                            "time": time_str,
                            "timestamp": timestamp
                        })

                except StaleElementReferenceException:
                    continue
                except Exception:
                    continue

        except Exception as e:
            print(f"[WhatsApp] _scrape_messages error: {e}")

        return messages

    def _type_and_send(self, message: str) -> bool:
        """Type a message and click Send in the currently open chat."""
        try:
            msg_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@contenteditable='true'][@role='textbox']")
                )
            )
            msg_box.click()
            time.sleep(0.5)
            msg_box.send_keys(message)
            time.sleep(1)
            return self._click_send(msg_box)
        except Exception as e:
            print(f"[WhatsApp] _type_and_send error: {e}")
            return False

    def _click_send(self, fallback_element=None) -> bool:
        """Click the Send button, or press Enter as fallback."""
        try:
            send_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@aria-label='Send']")
                )
            )
            send_btn.click()
            print("[WhatsApp] ✅ Message sent!")
            time.sleep(2)
            return True
        except TimeoutException:
            if fallback_element:
                fallback_element.send_keys(Keys.ENTER)
                print("[WhatsApp] ✅ Message sent (Enter key)!")
                time.sleep(2)
                return True
            print("[WhatsApp] ❌ Could not find Send button.")
            return False


# ─────────────────────────────────────────────────────────────
#  ROSYAI / JARVISAI  INTEGRATION HELPER
# ─────────────────────────────────────────────────────────────

class WhatsAppPlugin:
    """
    Drop-in plugin adapter for RosyAI / JarvisAI.

    Usage inside your AI class:
        self.whatsapp = WhatsAppPlugin(ai_instance=self)
        self.whatsapp.start()

    Rosy/Jarvis can then call:
        self.whatsapp.send("Alice", "Hello!")
        self.whatsapp.read("Alice")
        self.whatsapp.who_messaged()        → "Alice sent: Hey Rosy!"
        self.whatsapp.listen()              → starts auto-monitor → Rosy replies
    """

    def __init__(self, ai_instance=None, headless: bool = True):
        self.wa = WhatsAppRosy()
        self.ai = ai_instance           # your RosyAI / JarvisAI object
        self.headless = headless
        self._active = False

    def start(self) -> bool:
        ok = self.wa.start(headless=self.headless)
        if ok:
            self._active = True
        return ok

    def stop(self):
        self.wa.close()
        self._active = False

    # ── Send ──────────────────────────────────────
    def send(self, contact: str, message: str, by_number: bool = False) -> bool:
        """Unified send — auto-detects phone number vs name."""
        if contact.startswith("+") or contact.replace(" ", "").isdigit():
            return self.wa.send_by_number(contact, message)
        return self.wa.send_by_name(contact, message)

    # ── Read ──────────────────────────────────────
    def read(self, contact: str, count: int = 5) -> list[dict]:
        """Return last N messages from contact."""
        return self.wa.get_latest_messages(contact, count)

    def read_pretty(self, contact: str, count: int = 5) -> str:
        """Return messages as a human-readable string for Rosy/Jarvis."""
        msgs = self.read(contact, count)
        if not msgs:
            return f"No messages found from {contact}."
        lines = [f"=== Last {len(msgs)} messages with {contact} ==="]
        for m in msgs:
            who = "You" if m["sender"] == "me" else contact
            lines.append(f"[{m['time']}] {who}: {m['text']}")
        return "\n".join(lines)

    def who_messaged(self) -> str:
        """
        Tell Rosy/Jarvis who has unread messages right now.
        Returns a natural-language summary.
        """
        unread = self.wa.get_unread_chats()
        if not unread:
            return "No new WhatsApp messages."
        parts = []
        for item in unread:
            n = item["unread_count"]
            parts.append(f"{item['name']} sent {n} message{'s' if n > 1 else ''}")
        return "WhatsApp: " + ", ".join(parts) + "."

    def last_message_from(self, contact: str) -> str:
        """Get the single latest message — useful for Rosy voice responses."""
        msg = self.wa.get_last_message(contact)
        if not msg:
            return f"No messages from {contact}."
        who = "You" if msg["sender"] == "me" else contact
        return f"{who} said at {msg['time']}: {msg['text']}"

    # ── Auto-listen & reply ───────────────────────
    def listen(self, contacts: list[str] | None = None):
        """
        Start background monitoring. When a new message arrives, Rosy/Jarvis
        auto-generates a reply (if self.ai has a .respond() or .think() method).

        Override `_ai_reply()` if your AI class uses a different method name.
        """
        self.wa.start_monitoring(
            callback=self._handle_incoming,
            contacts=contacts
        )

    def _handle_incoming(self, event: dict):
        """Called automatically when a new message arrives."""
        contact = event["contact"]
        text = event["text"]
        print(f"\n[RosyAI] 📩 {contact}: {text}")

        if self.ai is not None:
            reply = self._ai_reply(text, contact)
            if reply:
                self.wa.send_by_name(contact, reply)
                print(f"[RosyAI] 💬 Replied to {contact}: {reply[:60]}")

    def _ai_reply(self, text: str, contact: str) -> str | None:
        """
        Bridge to your AI's response method.
        Customize this to match your AI class API.
        """
        # Try common AI method names
        prompt = f"WhatsApp message from {contact}: {text}"
        for method in ("respond", "think", "chat", "reply", "ask", "process"):
            fn = getattr(self.ai, method, None)
            if callable(fn):
                return fn(prompt)
        return None


# ─────────────────────────────────────────────────────────────
#  STANDALONE DEMO  (run this file directly to test)
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  WhatsApp Module — RosyAI / JarvisAI")
    print("=" * 60)

    wa = WhatsAppRosy()
    if not wa.start(headless=True):
        print("Could not start. Make sure you have scanned the QR code first.")
        exit(1)

    # ── Demo 1: Read latest messages ──────────────────────────
    print("\n[Demo 1] Reading last 5 messages from a contact…")
    msgs = wa.get_latest_messages("John Doe", count=5)
    for m in msgs:
        who = "Me" if m["sender"] == "me" else "John Doe"
        print(f"  [{m['time']}] {who}: {m['text']}")

    # ── Demo 2: Who has messaged me? ──────────────────────────
    print("\n[Demo 2] Checking unread chats…")
    unread = wa.get_unread_chats()
    if unread:
        for item in unread:
            print(f"  {item['name']} — {item['unread_count']} unread")
    else:
        print("  No unread messages.")

    # ── Demo 3: Send a reply ──────────────────────────────────
    print("\n[Demo 3] Sending a message…")
    wa.send_by_name("John Doe", "Hey! This is Rosy 🤖")

    # ── Demo 4: Background monitor ────────────────────────────
    print("\n[Demo 4] Starting background monitor for 30 seconds…")

    def my_handler(event):
        print(f"  🔔 New message from {event['contact']}: {event['text']}")
        # Auto-reply example:
        # wa.send_by_name(event['contact'], "Rosy is busy, I'll reply soon!")

    wa.start_monitoring(callback=my_handler)
    time.sleep(30)
    wa.stop_monitoring()

    wa.close()
    print("\n[+] Done!")