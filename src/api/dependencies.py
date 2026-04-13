"""
API dependencies — auth guards, DB session injection.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from config.settings import settings
from src.db.session import get_db
from src.db.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Extract and validate current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_faculty_user(user: User = Depends(get_current_user)) -> User:
    """Require faculty or admin role."""
    if user.role not in [UserRole.FACULTY, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Faculty access required")
    return user


def get_current_student_user(user: User = Depends(get_current_user)) -> User:
    """Require student role."""
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Student access required")
    return user


def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    """Require admin or privacy officer role."""
    if user.role not in [UserRole.ADMIN, UserRole.PRIVACY_OFFICER]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
