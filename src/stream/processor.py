"""
Main video stream orchestrator.
Runs all three AI modules (face recognition, engagement, phone detection)
on each frame from the classroom camera.
"""
import cv2
import asyncio
import time
import threading
from typing import Optional, Callable
from src.face_recognition.recognizer import AttendanceRecognizer, StudentEmbeddingDatabase
from src.engagement.head_pose import HeadPoseEstimator
from src.engagement.gaze_tracker import compute_iris_gaze
from src.engagement.classifier import StudentEngagementTracker
from src.detection.phone_detector import PhoneDetector
from src.stream.zone_mapper import ZoneMapper
from src.stream.camera_manager import CameraManager
from config.settings import settings
from config.constants import AttendanceStatus, FailureCode
from src.utils.logger import logger
import mediapipe as mp

mp_face_mesh_module = mp.solutions.face_mesh


class SessionProcessor:
    """
    Runs a complete class session:
    1. Opens camera
    2. For each frame: recognize faces, classify engagement, detect phones
    3. Marks attendance within SCAN_WINDOW_MINUTES (US-02)
    4. Continues engagement monitoring for session duration
    5. Saves results to DB and pushes to WebSocket
    """

    def __init__(
        self,
        session_id: str,
        batch_id: str,
        on_attendance_update: Callable,
        on_attendance_sync: Callable,
        on_phone_alert: Callable,
        on_session_complete: Callable,
    ):
        self.session_id = session_id
        self.batch_id = batch_id
        self.on_attendance_update = on_attendance_update
        self.on_attendance_sync = on_attendance_sync
        self.on_phone_alert = on_phone_alert
        self.on_session_complete = on_session_complete

        # Subsystems
        self.db = StudentEmbeddingDatabase()
        self.recognizer = AttendanceRecognizer(self.db)
        self.head_pose_estimator = HeadPoseEstimator()
        self.phone_detector = PhoneDetector()
        self.zone_mapper = ZoneMapper(rows=4, cols=3)
        self.camera = CameraManager()

        # State
        self.attendance_marked: dict = {}
        self.engagement_trackers: dict = {}
        self.scan_complete = False
        self.session_start_time: Optional[float] = None
        self._running = False

        self.face_mesh = mp_face_mesh_module.FaceMesh(
            max_num_faces=30,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def start(self):
        """Start session in a background thread."""
        self.db.load_all()
        self.session_start_time = time.time()
        self._running = True
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()
        logger.info(f"Session {self.session_id} started")

    def stop(self):
        """Stop the session and trigger heatmap generation."""
        self._running = False
        session_summaries = {
            roll: tracker.get_session_summary()
            for roll, tracker in self.engagement_trackers.items()
        }
        self.on_session_complete(self.session_id, session_summaries)
        logger.info(f"Session {self.session_id} stopped")

    def _run_loop(self):
        """Main processing loop."""
        try:
            self.camera.open(settings.CAMERA_INDEX, settings.CAMERA_FPS)
        except RuntimeError as e:
            logger.error(f"Camera failed to open: {e}")
            self.on_attendance_update(self.session_id, {
                "status": AttendanceStatus.INCOMPLETE_SCAN,
                "failure_code": FailureCode.CAMERA_LOST,
                "attendance": self.attendance_marked
            })
            return

        frame_count = 0
        while self._running:
            frame = self.camera.read_frame()
            if frame is None:
                logger.warning("Camera frame dropped")
                continue

            now = time.time()
            elapsed = now - self.session_start_time
            frame_count += 1

            scan_deadline = settings.SCAN_WINDOW_MINUTES * 60
            late_deadline = settings.LATE_WINDOW_MINUTES * 60

            if elapsed <= scan_deadline and not self.scan_complete:
                self._process_attendance_frame(frame, now, is_late=False)
                if frame_count % (settings.CAMERA_FPS * 30) == 0:
                    self.on_attendance_update(self.session_id, {
                        "present_count": sum(
                            1 for s in self.attendance_marked.values()
                            if s in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]
                        ),
                        "attendance": self.attendance_marked
                    })

            elif elapsed <= late_deadline and not self.scan_complete:
                self._process_attendance_frame(frame, now, is_late=True)

            elif not self.scan_complete:
                self.scan_complete = True
                self.on_attendance_update(self.session_id, {
                    "scan_complete": True,
                    "attendance": self.attendance_marked
                })

            # Engagement monitoring (every 3rd frame)
            if frame_count % 3 == 0:
                self._process_engagement_frame(frame, now)

            # Periodic Attendance Sync to DB (every 10 seconds)
            if frame_count % (settings.CAMERA_FPS * 10) == 0:
                self.on_attendance_sync(self.session_id, self.attendance_marked)

            # Phone detection (every frame)
            phone_detections = self.phone_detector.detect(frame, now)
            for det in phone_detections:
                det.zone = self.zone_mapper.get_zone_for_bbox(det.bbox, frame.shape)
                self.on_phone_alert(self.session_id, {
                    "zone": det.zone,
                    "confidence": det.confidence,
                    "timestamp": now,
                    "bbox": det.bbox
                })

            time.sleep(max(0, (1.0 / settings.CAMERA_FPS) - 0.01))

        self.camera.close()

    def _process_attendance_frame(self, frame, timestamp: float, is_late: bool):
        """Run face recognition and update attendance dict."""
        recognition_results = self.recognizer.process_frame(frame)
        
        # Log detection density for debugging US-01
        if not recognition_results:
            # We don't log "no faces" every frame to avoid log spam, 
            # but we could log it every few seconds
            return

        for result in recognition_results:
            roll = result.roll_number
            
            # Debug log for Samyak or any low-confidence matches
            if roll == "BT23CSE001" or (roll is None and result.confidence > 0.1):
                logger.debug(
                    f"RECOGNITION: roll={roll} conf={result.confidence:.2f} "
                    f"status={result.status} failure={result.failure_code}"
                )

            if roll is None:
                continue

            # Update in-memory dict with full details
            current_status = self.attendance_marked.get(roll, {}).get("status")
            
            if current_status not in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]:
                status = result.status
                if status == AttendanceStatus.PRESENT and is_late:
                    status = AttendanceStatus.LATE
                
                self.attendance_marked[roll] = {
                    "status": status,
                    "confidence": result.confidence,
                    "failure_code": result.failure_code,
                    "used_upper": result.used_upper_face_only
                }

    def _process_engagement_frame(self, frame, timestamp: float):
        """Run head pose + gaze → engagement classification."""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mesh_results = self.face_mesh.process(frame_rgb)
        if not mesh_results.multi_face_landmarks:
            return

        pose_results = self.head_pose_estimator.estimate(frame)
        for i, face_lms in enumerate(mesh_results.multi_face_landmarks):
            pose = pose_results[i] if i < len(pose_results) else None
            gaze = compute_iris_gaze(face_lms, frame.shape[1], frame.shape[0])
            zone = self.zone_mapper.get_zone_for_landmarks(face_lms, frame.shape)
            tracker_key = zone or f"zone_{i}"

            if tracker_key not in self.engagement_trackers:
                self.engagement_trackers[tracker_key] = StudentEngagementTracker(tracker_key)

            self.engagement_trackers[tracker_key].classify(pose, gaze)
