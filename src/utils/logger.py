"""
Loguru-based logging configuration for FOCUS.
All modules should use: from src.utils.logger import logger
"""
import sys
from loguru import logger
from pathlib import Path

# Remove default handler
logger.remove()

# Console handler with color
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True
)

# File handler
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logger.add(
    str(log_dir / "focus_{time:YYYY-MM-DD}.log"),
    rotation="1 day",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO"
)

# Audit log (immutable, never rotated out during retention period)
logger.add(
    str(log_dir / "audit.log"),
    rotation="100 MB",
    retention="5 years",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | AUDIT | {message}",
    level="INFO",
    filter=lambda record: "audit" in record["extra"]
)


def audit_log(message: str):
    """Write to immutable audit log. Used for attendance overrides, consent changes, exports."""
    logger.bind(audit=True).info(message)
