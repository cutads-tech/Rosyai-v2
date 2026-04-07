import cv2
import os

FACE_DB = "auth/owner_face.pkl"

def who_is_here():
    """Return 'owner', 'unknown_person', 'no_one', or 'camera_error'."""
    try:
        import pickle
        import face_recognition
    except ImportError:
        return "face_recognition_not_installed"

    if not os.path.exists(FACE_DB):
        return "no_face_db"

    try:
        with open(FACE_DB, "rb") as f:
            owner_face = pickle.load(f)
    except Exception:
        return "face_db_error"

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        return "camera_error"

    ret, frame = cam.read()
    cam.release()

    if not ret:
        return "camera_error"

    rgb = frame[:, :, ::-1]
    try:
        import face_recognition
        encodings = face_recognition.face_encodings(rgb)
        if not encodings:
            return "no_one"
        for enc in encodings:
            match = face_recognition.compare_faces([owner_face], enc, tolerance=0.45)
            if match[0]:
                return "owner"
    except Exception:
        return "recognition_error"

    return "unknown_person"

# ✅ BUG FIXED: who_is_here() was auto-called at module bottom — removed.
