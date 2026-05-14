from dotenv import load_dotenv
import os

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from databases.connection import SessionLocal
from models.models import Student, User
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

router = APIRouter()
load_dotenv()

# =========================
# CONFIG JWT
# =========================
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()

def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_key_pem, public_key_pem

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
    user_role = payload.get("role")

    if user_role == "student":
        user = db.query(Student).filter(Student.id == user_id).first()
    else:
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
    
    private_key_rsa = None
    public_key_rsa = None

    if payload.role == "university":
        private_key_rsa, public_key_rsa = generate_rsa_keys()

    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hashed_password,
        role=payload.role,
        university_id=payload.university_id if payload.university_id else None,
        public_key=public_key_rsa if payload.role == "university" else None,
        created_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    response_data = {
        "message": "Registration successful",
        "data": UserData.model_validate(new_user)
    }

    if payload.role == "university":
        response_data["private_key"] = private_key_rsa
        response_data["private_key_instruction"] = "Store this key securely. This key is required to sign diplomas."

    return response_data

# =========================
# LOGIN
# =========================
@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    is_student = False

    if not user:
        user = db.query(Student).filter(Student.email == payload.email).first()
        is_student = True

    if not user:
        raise HTTPException(
            status_code=404,
            detail={"message": "Email not registered"}
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid credentials"}
        )
    
    role = "student" if is_student else user.role
    university_id = None if is_student else user.university_id

    if role == "university" and not university_id:
        raise HTTPException(
            status_code=400,
            detail={"message": "University user must have a university_id"}
        )

    access_token = create_access_token({
        "user_id": user.id,
        "email": user.email,
        "role": role,
        "university_id": university_id
    })

    return {
        "message": "Login successful",
        "data": {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": role,
                "university_id": university_id,
                "is_phone_verified": getattr(user, 'is_phone_verified', None) if is_student else None
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
    }