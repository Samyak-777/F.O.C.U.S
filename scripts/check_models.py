"""
Verify all pre-trained models are accessible before first run.
Run this before starting the system for the first time.
"""
print("Checking FOCUS model dependencies...\n")

# 1. InsightFace buffalo_l
try:
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=(160, 160))
    print("✅ InsightFace buffalo_l (ArcFace): OK")
except Exception as e:
    print(f"❌ InsightFace buffalo_l: FAILED — {e}")
    print("   Fix: pip install insightface onnxruntime")

# 2. MediaPipe FaceMesh
try:
    import mediapipe as mp
    mp.solutions.face_mesh.FaceMesh(max_num_faces=1)
    print("✅ MediaPipe FaceMesh (head pose + gaze): OK")
except Exception as e:
    print(f"❌ MediaPipe FaceMesh: FAILED — {e}")
    print("   Fix: pip install mediapipe")

# 3. YOLOv8n
try:
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")
    print("✅ YOLOv8n (phone detection): OK")
except Exception as e:
    print(f"❌ YOLOv8n: FAILED — {e}")
    print("   Fix: pip install ultralytics")

# 4. OpenCV
try:
    import cv2
    print(f"✅ OpenCV {cv2.__version__}: OK")
except Exception as e:
    print(f"❌ OpenCV: FAILED — {e}")

print("\nAll checks complete.")
