import pyautogui
import pytesseract
import cv2
import numpy as np
import time
import os
from PIL import Image
from ultralytics import YOLO

# ── Tesseract path (env-overridable) ─────────────────────────────
TESSERACT_CMD = os.environ.get(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# ── YOLO model ────────────────────────────────────────────────────
_yolo = None
def _get_yolo():
    global _yolo
    if _yolo is None:
        try:
            _yolo = YOLO("yolov8n.pt")
        except Exception as e:
            print(f"[screen_vision] YOLO load error: {e}")
    return _yolo


# ═══════════════════════════════════════════════
# CAPTURE
# ═══════════════════════════════════════════════
def capture_screen(region=None):
    """Capture full screen or a (x, y, w, h) region. Returns numpy array."""
    try:
        if region:
            shot = pyautogui.screenshot(region=region)
        else:
            shot = pyautogui.screenshot()
        return np.array(shot)
    except Exception as e:
        print(f"[screen_vision] capture_screen error: {e}")
        return np.zeros((100, 100, 3), dtype=np.uint8)


# ═══════════════════════════════════════════════
# PRE-PROCESSING (improves OCR accuracy)
# ═══════════════════════════════════════════════
def preprocess(img: np.ndarray) -> np.ndarray:
    """Convert to grayscale, denoise, adaptive threshold for OCR."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return thresh


# ═══════════════════════════════════════════════
# OCR
# ═══════════════════════════════════════════════
def read_screen_text(region=None) -> str:
    """OCR the full screen (or region) and return text."""
    try:
        img = capture_screen(region)
        processed = preprocess(img)
        config = "--psm 6 -l eng+hin"   # support Hindi + English
        text = pytesseract.image_to_string(processed, config=config)
        return text.strip()
    except Exception as e:
        return f"[OCR error: {e}]"


def find_text(target: str, region=None):
    """Find screen coordinates of target text. Returns dict or None."""
    try:
        img = capture_screen(region)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        for i, word in enumerate(data["text"]):
            if target.lower() in (word or "").lower() and int(data["conf"][i]) > 40:
                x, y = data["left"][i], data["top"][i]
                w, h = data["width"][i], data["height"][i]
                offset_x = region[0] if region else 0
                offset_y = region[1] if region else 0
                return {
                    "text": word, "conf": data["conf"][i],
                    "x": x + offset_x, "y": y + offset_y,
                    "width": w, "height": h
                }
    except Exception as e:
        print(f"[screen_vision] find_text error: {e}")
    return None


# ═══════════════════════════════════════════════
# SMART CLICK
# ═══════════════════════════════════════════════
def smart_click(text: str) -> bool:
    """Find text on screen and click its center."""
    result = find_text(text)
    if result:
        cx = result["x"] + result["width"] // 2
        cy = result["y"] + result["height"] // 2
        pyautogui.moveTo(cx, cy, duration=0.15)
        pyautogui.click()
        return True
    return False


# ═══════════════════════════════════════════════
# GUI / OBJECT DETECTION (YOLO)
# ═══════════════════════════════════════════════
def detect_gui_elements(confidence: float = 0.3) -> list:
    """Run YOLO on screen, return list of detected object dicts."""
    model = _get_yolo()
    if model is None:
        return []
    try:
        img = capture_screen()
        results = model(img, verbose=False, conf=confidence)
        objects = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                objects.append({
                    "name": model.names[cls],
                    "x":  (x1 + x2) // 2,
                    "y":  (y1 + y2) // 2,
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "confidence": float(box.conf[0])
                })
        return objects
    except Exception as e:
        print(f"[screen_vision] detect_gui_elements error: {e}")
        return []


def click_object(index: int = 0) -> bool:
    objects = detect_gui_elements()
    if not objects or index >= len(objects):
        return False
    obj = objects[index]
    pyautogui.moveTo(obj["x"], obj["y"], duration=0.15)
    pyautogui.click()
    return True


# ═══════════════════════════════════════════════
# WINDOW DETECTION (contour-based)
# ═══════════════════════════════════════════════
def detect_windows() -> list:
    """Detect large rectangular regions (windows) via edge detection."""
    img = capture_screen()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    windows = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w > 300 and h > 200:
            windows.append({"x": x, "y": y, "width": w, "height": h})
    return windows


# ═══════════════════════════════════════════════
# FULL SCREEN DESCRIPTION
# ═══════════════════════════════════════════════
def describe_screen() -> dict:
    """Return a unified description: text, object count, window count."""
    text = read_screen_text()
    objects = detect_gui_elements()
    windows = detect_windows()
    return {
        "visible_text":     text[:500],
        "objects_detected": len(objects),
        "windows_detected": len(windows),
        "top_objects":      [o["name"] for o in objects[:5]],
    }


# ═══════════════════════════════════════════════
# SCREENSHOT SAVE
# ═══════════════════════════════════════════════
def save_screenshot(path: str = None) -> str:
    """Save a screenshot and return the file path."""
    if path is None:
        path = f"screenshot_{int(time.time())}.png"
    img = capture_screen()
    Image.fromarray(img).save(path)
    return path
