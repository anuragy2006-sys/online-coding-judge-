import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, SESSION_COOKIE_NAME, SESSION_MAX_AGE
from app.database import get_db
from app import models

serializer = URLSafeTimedSerializer(SECRET_KEY, salt="judge-session")

# bcrypt has a hard 72-byte input limit; truncate defensively (passwords
# longer than that are astronomically rare and this avoids a hard crash).
_MAX_BCRYPT_BYTES = 72


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")[:_MAX_BCRYPT_BYTES]
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pw_bytes = plain.encode("utf-8")[:_MAX_BCRYPT_BYTES]
    try:
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
    except ValueError:
        return False


def create_session_token(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})


def read_session_token(token: str):
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data.get("user_id")
    except (BadSignature, SignatureExpired):
        return None


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    user_id = read_session_token(token)
    if not user_id:
        return None
    return db.query(models.User).filter(models.User.id == user_id).first()


def set_no_store_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def set_session_cookie(response, user_id: int):
    from app.config import COOKIE_SECURE
    response.set_cookie(
        SESSION_COOKIE_NAME, create_session_token(user_id), max_age=SESSION_MAX_AGE,
        httponly=True, samesite="lax", secure=COOKIE_SECURE,
    )
    return response


def require_user(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user


def require_admin(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not (user.is_admin or user.role == "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_staff(request: Request, db: Session = Depends(get_db)):
    """Faculty or admin."""
    user = get_current_user(request, db)
    if not user or not user.is_staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faculty or admin access required")
    return user


def require_user_json(request: Request, db: Session = Depends(get_db)):
    """For JSON APIs: 401 instead of an HTML redirect."""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in.")
    return user
