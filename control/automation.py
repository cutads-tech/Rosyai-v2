import time
import logging
from typing import Optional, Tuple

try:
    import pyautogui
except Exception as e:
    raise RuntimeError("pyautogui is required for automation.py") from e

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

logger = logging.getLogger(__name__)
if not logger.handlers:
    h = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s [automation] %(levelname)s: %(message)s")
    h.setFormatter(fmt)
    logger.addHandler(h)
logger.setLevel(logging.INFO)


def move_mouse(x: int, y: int, duration: float = 0.2) -> None:
    """Move mouse to (x, y) with a small duration."""
    try:
        pyautogui.moveTo(int(x), int(y), duration=duration)
    except Exception as e:
        logger.exception("move_mouse failed: %s", e)


def click(x: Optional[int] = None, y: Optional[int] = None, clicks: int = 1, interval: float = 0.0, button: str = "left") -> bool:
    """Click at (x,y) if provided, otherwise click current position."""
    try:
        if x is not None and y is not None:
            pyautogui.click(int(x), int(y), clicks=clicks, interval=interval, button=button)
        else:
            pyautogui.click(clicks=clicks, interval=interval, button=button)
        return True
    except Exception as e:
        logger.exception("click failed: %s", e)
        return False


def double_click(x: Optional[int] = None, y: Optional[int] = None) -> bool:
    return click(x, y, clicks=2, interval=0.1)


def right_click(x: Optional[int] = None, y: Optional[int] = None) -> bool:
    return click(x, y, clicks=1, button="right")


def drag_to(x: int, y: int, duration: float = 0.4) -> bool:
    try:
        pyautogui.dragTo(int(x), int(y), duration=duration)
        return True
    except Exception as e:
        logger.exception("drag_to failed: %s", e)
        return False


def type_text(text: str, interval: float = 0.03, use_clipboard_fallback: bool = True) -> bool:
    """
    Type text with a small interval. If typing fails (some special characters),
    uses clipboard paste fallback when allowed.
    """
    try:
        pyautogui.write(str(text), interval=interval)
        return True
    except Exception as e:
        logger.warning("pyautogui.write failed (%s). Trying clipboard fallback.", e)
        if use_clipboard_fallback:
            try:
                import pyperclip
                pyperclip.copy(str(text))
                pyautogui.hotkey('ctrl', 'v')
                return True
            except Exception as e2:
                logger.exception("clipboard fallback failed: %s", e2)
                return False
        return False


def press_key(key: str) -> None:
    try:
        pyautogui.press(key)
    except Exception as e:
        logger.exception("press_key failed: %s", e)


def hotkey(*keys: str) -> None:
    try:
        pyautogui.hotkey(*keys)
    except Exception as e:
        logger.exception("hotkey failed: %s", e)


def scroll(amount: int) -> None:
    try:
        pyautogui.scroll(int(amount))
    except Exception as e:
        logger.exception("scroll failed: %s", e)


def open_run() -> None:
    """Open Windows Run dialog (win + r)."""
    try:
        hotkey('win', 'r')
    except Exception:
        # fallback to press win then r (best-effort)
        press_key('win')
        time.sleep(0.05)
        press_key('r')


def open_start_menu() -> None:
    try:
        press_key('win')
    except Exception as e:
        logger.exception("open_start_menu failed: %s", e)


def screenshot(region: Optional[Tuple[int, int, int, int]] = None, path: Optional[str] = None):
    """Take a screenshot. If path provided, save to disk."""
    try:
        im = pyautogui.screenshot(region=region)
        if path:
            im.save(path)
            logger.info("Screenshot saved to %s", path)
        return im
    except Exception as e:
        logger.exception("screenshot failed: %s", e)
        return None


def locate_on_screen(image_path: str, confidence: float = 0.8, grayscale: bool = False, timeout: float = 5.0):
    """
    Locate image on screen. Returns box (left, top, width, height) or None.
    Uses a timeout loop to be more robust.
    """
    start = time.time()
    while True:
        try:
            box = pyautogui.locateOnScreen(image_path, confidence=confidence, grayscale=grayscale)
            if box:
                return box
        except Exception as e:
            # On some systems OpenCV not present — log and break
            logger.debug("locate_on_screen exception: %s", e)
        if time.time() - start > timeout:
            return None
        time.sleep(0.25)


def safe_click(image_path: Optional[str] = None, region=None, confidence: float = 0.8, timeout: float = 6.0, clicks: int = 1, button: str = "left") -> bool:
    """
    If image_path is provided, wait until it appears and click its center.
    Otherwise, click current position.
    """
    try:
        if image_path:
            box = locate_on_screen(image_path, confidence=confidence, timeout=timeout)
            if not box:
                logger.warning("safe_click: image not found %s", image_path)
                return False
            cx = box.left + box.width // 2
            cy = box.top + box.height // 2
            move_mouse(cx, cy, duration=0.12)
            return click(cx, cy, clicks=clicks, button=button)
        else:
            return click(clicks=clicks, button=button)
    except Exception as e:
        logger.exception("safe_click failed: %s", e)
        return False


def wait_for_image(image_path: str, confidence: float = 0.8, timeout: float = 10.0) -> bool:
    """Wait for an image to appear on screen within timeout."""
    return locate_on_screen(image_path, confidence=confidence, timeout=timeout) is not None