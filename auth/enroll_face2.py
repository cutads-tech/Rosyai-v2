import cv2
import face_recognition
import pickle
import time

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cam.isOpened():
    print("❌ Camera not accessible")
    exit()

print("📸 Preparing camera… please look straight")

# Warm-up camera
for _ in range(30):
    cam.read()
    time.sleep(0.05)

encodings = []

print("📸 Capturing face… stay still")

for i in range(10):
    ret, frame = cam.read()
    if not ret:
        continue

    # Convert BGR → RGB (VERY IMPORTANT)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_recognition.api.face_encodings(rgb, model="large")
    faces = face_recognition.face_encodings(rgb)

    if faces:
        encodings.append(faces[0])

    time.sleep(0.2)

cam.release()

if not encodings:
    print("❌ Face not detected.")
    print("Tips:")
    print("- Keep face centered")
    print("- Remove glasses / mask")
    print("- Don’t stay too close")
    print("- Look straight at camera")
    exit()

# Average multiple encodings (more accurate)
avg_encoding = sum(encodings) / len(encodings)

with open("auth/owner_face.pkl", "wb") as f:
    pickle.dump(avg_encoding, f)

print(f"✅ Face enrolled successfully using {len(encodings)} samples")
