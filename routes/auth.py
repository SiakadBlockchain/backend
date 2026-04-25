from dotenv import load_dotenv
import os

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from databases.connection import SessionLocal
from models.models import User
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
load_dotenv()

# =========================
# CONFIG JWT
# =========================
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# =========================
# JWT FUNCTIONS
# =========================
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# =========================
# AUTH DEPENDENCY
# =========================
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid or expired token"}
        )

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail={"message": "User not found"}
        )

    return user

# =========================
# SCHEMA
# =========================
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    university_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserData(BaseModel):
    id: str
    name: str
    email: str
    role: str
    university_id: Optional[str] = None

    class Config:
        from_attributes = True


# =========================
# REGISTER
# =========================
@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail={"message": "Email already registered"}
        )

    hashed_password = hash_password(payload.password)

    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hashed_password,
        role=payload.role,
        university_id=payload.university_id if payload.university_id else None
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Register success",
        "data": UserData.model_validate(new_user)
    }

# =========================
# LOGIN
# =========================
@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail={"message": "User not found"}
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid credentials"}
        )

    if user.role == "university" and not user.university_id:
        raise HTTPException(
            status_code=400,
            detail={"message": "University user must have university_id"}
        )

    access_token = create_access_token({
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "university_id": user.university_id
    })

    return {
        "message": "Login success",
        "data": {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "university_id": user.university_id
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
    }