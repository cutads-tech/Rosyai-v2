import cv2
import numpy as np
import pyautogui
from ultralytics import YOLO

model = YOLO("yolov8n.pt")


def capture_screen():
    img = pyautogui.screenshot()
    frame = np.array(img)
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def detect_objects():
    """Detect objects on screen. Returns list of dicts with name, x, y."""
    try:
        frame = capture_screen()
        results = model(frame, verbose=False)
        objects = []
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                name = model.names[cls]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                objects.append({
                    "name": name,
                    "x": int((x1 + x2) / 2),
                    "y": int((y1 + y2) / 2),
                    "confidence": float(box.conf[0])
                })
        return objects
    except Exception as e:
        print(f"[vision_yolo] detect_objects error: {e}")
        return []

# ✅ BUG FIX: `return objects` was on same line as preceding code — now properly separated.
