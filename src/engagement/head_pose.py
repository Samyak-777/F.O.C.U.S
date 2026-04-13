"""
Head pose estimation using MediaPipe FaceMesh.
Outputs yaw (left/right), pitch (up/down), roll (tilt) in degrees.
"""
import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass
from typing import Optional

mp_face_mesh = mp.solutions.face_mesh

# 3D model reference points
MODEL_POINTS = np.array([
    (0.0, 0.0, 0.0),             # Nose tip (landmark 1)
    (0.0, -330.0, -65.0),        # Chin (landmark 152)
    (-225.0, 170.0, -135.0),     # Left eye left corner (landmark 263)
    (225.0, 170.0, -135.0),      # Right eye right corner (landmark 33)
    (-150.0, -150.0, -125.0),    # Left mouth corner (landmark 287)
    (150.0, -150.0, -125.0),     # Right mouth corner (landmark 57)
], dtype=np.float64)

LANDMARK_INDICES = [1, 152, 263, 33, 287, 57]


@dataclass
class HeadPoseResult:
    yaw: float    # + = looking right, - = looking left (degrees)
    pitch: float  # + = looking up, - = looking down (degrees)
    roll: float   # tilt (degrees)
    confidence: float  # 0-1 based on landmark visibility


class HeadPoseEstimator:
    """Estimates 3D head pose from MediaPipe FaceMesh landmarks."""

    def __init__(self):
        self.face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=30,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            static_image_mode=False
        )

    def estimate(self, frame_bgr: np.ndarray) -> list:
        """Process one frame. Returns list of HeadPoseResult, one per detected face."""
        h, w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)

        camera_matrix = np.array([
            [w, 0, w / 2],
            [0, w, h / 2],
            [0, 0, 1]
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1))

        poses = []
        if not results.multi_face_landmarks:
            return poses

        for face_landmarks in results.multi_face_landmarks:
            image_points = []
            visibilities = []

            for idx in LANDMARK_INDICES:
                lm = face_landmarks.landmark[idx]
                image_points.append((lm.x * w, lm.y * h))
                visibilities.append(lm.visibility if hasattr(lm, 'visibility') else 1.0)

            image_points = np.array(image_points, dtype=np.float64)
            confidence = float(np.mean(visibilities))

            success, rotation_vec, translation_vec = cv2.solvePnP(
                MODEL_POINTS, image_points, camera_matrix, dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )

            if not success:
                continue

            rotation_mat, _ = cv2.Rodrigues(rotation_vec)
            pose_mat = cv2.hconcat([rotation_mat, translation_vec])
            _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)

            pitch = float(euler_angles[0])
            yaw = float(euler_angles[1])
            roll = float(euler_angles[2])

            poses.append(HeadPoseResult(
                yaw=yaw, pitch=pitch, roll=roll, confidence=confidence
            ))

        return poses
