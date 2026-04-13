"""
Session management endpoints.
POST /api/sessions/start  → start a class session
POST /api/sessions/{id}/stop  → end session, trigger heatmap
GET  /api/sessions/{id}   → session status
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_faculty_user, get_db
from src.db.session import SessionLocal
from src.db.crud import (
    create_session, get_session, update_session, 
    sync_session_attendance, create_phone_alert, save_engagement_records
)
from src.stream.processor import SessionProcessor
from src.analytics.heatmap import generate_heatmap
from src.api.websocket import broadcast_to_session
import asyncio

router = APIRouter()
_active_sessions: dict = {}


class StartSessionRequest(BaseModel):
    batch_id: str
    scheduled_start: datetime
    room_id: str


@router.post("/start")
def start_session(
    req: StartSessionRequest,
    faculty=Depends(get_current_faculty_user),
    db: Session = Depends(get_db)
):
    """US-02: Start automated attendance scan."""
    session = create_session(db, req.batch_id, faculty.id, req.scheduled_start)

    processor = SessionProcessor(
        session_id=str(session.id),
        batch_id=req.batch_id,
        on_attendance_update=_handle_attendance_update,
        on_attendance_sync=_handle_attendance_sync,
        on_phone_alert=_handle_phone_alert,
        on_session_complete=_handle_session_complete
    )
    processor.start()
    _active_sessions[str(session.id)] = processor

    return {"session_id": session.id, "status": "started", "message": "Attendance scan begun"}


@router.post("/{session_id}/stop")
def stop_session(
    session_id: str,
    faculty=Depends(get_current_faculty_user),
    db: Session = Depends(get_db)
):
    """Stop an active session and trigger heatmap generation."""
    if session_id not in _active_sessions:
        raise HTTPException(status_code=404, detail="Session not active")

    processor = _active_sessions.pop(session_id)
    # Perform one last sync before stopping
    _handle_attendance_sync(session_id, processor.attendance_marked)
    processor.stop()
    update_session(db, int(session_id), {"status": "completed", "ended_at": datetime.utcnow()})

    return {"session_id": session_id, "status": "completed"}


@router.get("/{session_id}")
def get_session_status(
    session_id: str,
    faculty=Depends(get_current_faculty_user),
    db: Session = Depends(get_db)
):
    """Get session details."""
    session = get_session(db, int(session_id))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    is_active = session_id in _active_sessions
    return {
        "session_id": session.id,
        "batch_id": session.batch_id,
        "status": session.status,
        "is_active": is_active,
        "scheduled_start": session.scheduled_start.isoformat() if session.scheduled_start else None,
        "actual_start": session.actual_start.isoformat() if session.actual_start else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None
    }


def _handle_attendance_update(session_id: str, data: dict):
    try:
        asyncio.get_event_loop().create_task(
            broadcast_to_session(session_id, {"type": "attendance", **data})
        )
    except RuntimeError:
        pass  # No event loop available (background thread)


def _handle_attendance_sync(session_id: str, attendance_dict: dict):
    """Persist background attendance results to DB."""
    db = SessionLocal()
    try:
        sync_session_attendance(db, int(session_id), attendance_dict)
    finally:
        db.close()


def _handle_phone_alert(session_id: str, data: dict):
    """Save phone alert to DB and broadcast."""
    db = SessionLocal()
    try:
        create_phone_alert(db, int(session_id), data.get("zone", "Unknown"), data.get("confidence", 0.0))
    finally:
        db.close()

    try:
        asyncio.get_event_loop().create_task(
            broadcast_to_session(session_id, {"type": "phone_alert", **data})
        )
    except RuntimeError:
        pass


def _handle_session_complete(session_id: str, summaries: dict):
    heatmap = generate_heatmap(session_id, summaries)
    
    # Persist Heatmap to DB
    db = SessionLocal()
    try:
        save_engagement_records(db, int(session_id), heatmap.get("zones", {}))
    finally:
        db.close()

    try:
        asyncio.get_event_loop().create_task(
            broadcast_to_session(session_id, {"type": "session_complete", "heatmap": heatmap})
        )
    except RuntimeError:
        pass
