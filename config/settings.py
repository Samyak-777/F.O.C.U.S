from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "FOCUS"
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DATABASE_URL: str = "sqlite:///./data/db/focus.db"

    CAMERA_INDEX: int = 0
    CAMERA_FPS: int = 10
    SCAN_WINDOW_MINUTES: int = 7
    LATE_WINDOW_MINUTES: int = 15

    RECOGNITION_CONFIDENCE_MIN: float = 0.80
    RECOGNITION_DISTANCE_MAX: float = 0.45

    YAW_PASSIVE_THRESHOLD: float = 20.0
    YAW_DISENGAGED_THRESHOLD: float = 35.0
    PITCH_DOWN_THRESHOLD: float = 25.0
    EYE_CONFIDENCE_MIN: float = 0.60
    FLIP_SUPPRESSION_WINDOW: int = 300
    FLIP_SUPPRESSION_MAX: int = 15

    PHONE_CONFIDENCE_THRESHOLD: float = 0.50
    PHONE_SUSTAINED_SECONDS: int = 5
    PHONE_CLASS_ID: int = 67

    ZONE_MIN_STUDENTS: int = 8
    HEATMAP_RETENTION_DAYS: int = 30
    HEATMAP_INTERVAL_MINUTES: int = 15

    EXPORT_RETENTION_YEARS: int = 5
    EXPORT_MAX_STUDENTS: int = 200

    BIOMETRIC_DELETION_HOURS: int = 24
    SUPPORTED_LANGUAGES: str = "en,hi,mr,te"

    EMBEDDING_ENCRYPTION_KEY: str = ""

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@focus.vnit.ac.in"

    class Config:
        env_file = ".env"


settings = Settings()
