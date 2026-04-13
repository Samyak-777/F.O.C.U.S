"""FastAPI application factory."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import auth, sessions, attendance, engagement, alerts, students, admin, enrollment
from src.api.websocket import router as ws_router
from src.db.session import create_tables


def create_app() -> FastAPI:
    app = FastAPI(
        title="FOCUS API",
        description="Facial Observation for Classroom Understanding and Surveillance",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(attendance.router, prefix="/api/attendance", tags=["attendance"])
    app.include_router(engagement.router, prefix="/api/engagement", tags=["engagement"])
    app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
    app.include_router(students.router, prefix="/api/students", tags=["students"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    app.include_router(enrollment.router, prefix="/api/enrollment", tags=["enrollment"])
    app.include_router(ws_router, prefix="/ws")

    @app.on_event("startup")
    async def startup():
        create_tables()

    return app


app = create_app()
