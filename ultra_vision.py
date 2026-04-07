import pyautogui
import cv2
import numpy as np
import pytesseract
from ultralytics import YOLO

model = YOLO("yolov8n.pt")


def capture_screen():
    img = pyautogui.screenshot()
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def detect_objects(frame):

    results = model(frame)[0]

    detections = []

    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls = int(box.cls[0])
        name = model.names[cls]

        detections.append({
            "name": name,
            "center": ((x1+x2)//2, (y1+y2)//2),
            "box": (x1, y1, x2, y2)
        })

    return detections


def read_text(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)

    return text.lower()


def find_target(target_name):

    frame = capture_screen()

    objects = detect_objects(frame)
    text = read_text(frame)

    # 1️⃣ search object
    for obj in objects:
        if target_name.lower() in obj["name"]:
            return obj["center"]

    # 2️⃣ fallback: search text
    if target_name.lower() in text:
        h, w, _ = frame.shape
        return (w//2, h//2)

    return None