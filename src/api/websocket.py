"""WebSocket for real-time dashboard updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

router = APIRouter()

# session_id → list of connected WebSocket clients
_connections: Dict[str, List[WebSocket]] = {}


@router.websocket("/session/{session_id}")
async def session_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    if session_id not in _connections:
        _connections[session_id] = []
    _connections[session_id].append(websocket)

    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        _connections[session_id].remove(websocket)


async def broadcast_to_session(session_id: str, data: dict):
    """Push data to all clients watching a session."""
    if session_id not in _connections:
        return
    dead = []
    for ws in _connections[session_id]:
        try:
            await ws.send_text(json.dumps(data, default=str))
        except Exception:
            dead.append(ws)
    for ws in dead:
        _connections[session_id].remove(ws)
