import cv2
import face_recognition
import pickle

def get_camera():
    for i in range(5):
        cam = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cam.isOpened():
            print(f"✅ Camera found at index {i}")
            return cam
    return None

cam = get_camera()
if cam is None:
    print("❌ No camera detected")
    exit()

print("Look at camera… Press S to save face")

while True:
    ret, frame = cam.read()
    if not ret:
        continue

    cv2.imshow("Enroll Face", frame)

    if cv2.waitKey(1) & 0xFF == ord('s'):
        enc = face_recognition.face_encodings(frame)
        if enc:
            with open("auth/owner_face.pkl", "wb") as f:
                pickle.dump(enc[0], f)
            print("✅ Face enrolled successfully")
            break
        else:
            print("⚠️ Face not detected, try again")

cam.release()
cv2.destroyAllWindows()
