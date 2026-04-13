"""Authentication routes — login, register, JWT token generation."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from config.settings import settings
from src.db.session import get_db
from src.db.crud import create_user, get_user_by_email, verify_password
from src.db.models import UserRole

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "student"
    roll_number: str | None = None
    is_minor: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    role_map = {
        "student": UserRole.STUDENT,
        "faculty": UserRole.FACULTY,
        "admin": UserRole.ADMIN,
        "privacy_officer": UserRole.PRIVACY_OFFICER
    }
    role = role_map.get(req.role, UserRole.STUDENT)

    user = create_user(db, req.name, req.email, req.password, role,
                       req.roll_number, req.is_minor)
    return {"status": "registered", "user_id": user.id, "role": user.role.value}


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(db, form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token({"sub": user.email, "role": user.role.value})
    return TokenResponse(
        access_token=token,
        role=user.role.value,
        name=user.name
    )
