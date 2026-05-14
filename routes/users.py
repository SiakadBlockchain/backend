import hashlib

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from databases.connection import SessionLocal
from models.models import User
from typing import List, Optional
from pydantic import BaseModel
from passlib.context import CryptContext

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# =========================
# SCHEMA
# =========================
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    university_id: Optional[str] = None

class UserUpdate(BaseModel):
    name: str
    email: str
    password: Optional[str] = None
    role: str
    university_id: Optional[str] = None

class UserData(BaseModel):
    id: str
    name: str
    email: str
    role: str
    university_id: Optional[str] = None

    class Config:
        from_attributes = True

class ResponseModel(BaseModel):
    message: str
    data: Optional[dict] = None

# =========================
# CREATE USER
# =========================
@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail={"message": "Email already registered"}
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
        university_id=user.university_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "data": UserData.model_validate(new_user)
    }


# =========================
# GET ALL USERS
# =========================
@router.get("/")
def get_users(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    skip = (page - 1) * limit

    total = db.query(User).count()
    users = db.query(User).offset(skip).limit(limit).all()

    return {
        "message": "Users fetched successfully",
        "data": [UserData.model_validate(u) for u in users],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total
        }
    }


# =========================
# GET USER BY ID
# =========================
@router.get("/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail={"message": "User not found"}
        )

    return {
        "message": "User fetched successfully",
        "data": UserData.model_validate(user)
    }


# =========================
# UPDATE USER
# =========================
@router.put("/{user_id}")
def update_user(user_id: str, updated_user: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = updated_user.name
    user.email = updated_user.email
    user.role = updated_user.role
    user.university_id = updated_user.university_id

    if updated_user.password:
        user.password_hash = hash_password(updated_user.password)

    db.commit()
    db.refresh(user)
    return {"message": "User updated successfully", "data": UserData.model_validate(user)}


# =========================
# DELETE USER
# =========================
@router.delete("/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail={"message": "User not found"}
        )

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully"
    }