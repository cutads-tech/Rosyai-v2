import face_recognition, pickle, cv2

def verify_face():
    with open("auth/owner_face.pkl", "rb") as f:
        known = pickle.load(f)

    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        return False

    enc = face_recognition.face_encodings(frame)
    if not enc:
        return False

    return face_recognition.compare_faces([known], enc[0])[0]
if __name__ == "__main__":
    print("👤 Testing face authentication…")
    print("Verified:", verify_face())
