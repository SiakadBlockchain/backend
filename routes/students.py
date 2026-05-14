import asyncio
import os
from flask.cli import load_dotenv
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from databases.connection import SessionLocal
from models.models import Student
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from .diplomas import DiplomaData
from .wallets import generate_otp_code, send_otp_to_console
from .utils.helpers import auto_cleanup_otp
from datetime import datetime, timedelta

from cryptography.fernet import Fernet

load_dotenv()

MASTER_KEY = os.getenv("MASTER_KEY")
if not MASTER_KEY:
    raise ValueError("MASTER_KEY not found in environment variables")
cipher_suite = Fernet(MASTER_KEY.encode())

router = APIRouter()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def generate_student_rsa_keys():
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

# =========================
# SCHEMA
# =========================
class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    ktp_number: str
    phone_number: str
    place_and_date_of_birth: str

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    place_and_date_of_birth: Optional[str] = None

class WalletData(BaseModel):
    id: str
    blockchain_address: str
    is_connected: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

class StudentData(BaseModel):
    id: str
    name: str
    public_key: Optional[str]
    ktp_number: Optional[str]
    phone_number: str
    is_phone_verified: bool
    place_and_date_of_birth: Optional[str]
    email: str
    created_at: Optional[datetime]
    wallet: Optional[WalletData] = None

    class Config:
        from_attributes = True

# =========================
# CREATE STUDENT (REGISTER)
# =========================
@router.post("")
def register_student(
    payload: StudentCreate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    if db.query(Student).filter(Student.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(Student).filter(Student.ktp_number == payload.ktp_number).first():
        raise HTTPException(status_code=400, detail="Identity number already registered")

    if db.query(Student).filter(Student.phone_number == payload.phone_number).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    priv_rsa, pub_rsa = generate_student_rsa_keys()
    encrypted_rsa_priv = cipher_suite.encrypt(priv_rsa.encode()).decode()
    otp_code = generate_otp_code()

    new_student = Student(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        ktp_number=payload.ktp_number,
        phone_number=payload.phone_number,
        place_and_date_of_birth=payload.place_and_date_of_birth,
        public_key=pub_rsa,
        rsa_private_key_encrypted=encrypted_rsa_priv,
        is_phone_verified=False,
        created_at=datetime.utcnow(),
        otp_secret=otp_code
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    send_otp_to_console(new_student.phone_number, otp_code)

    background_tasks.add_task(auto_cleanup_otp, new_student.id, SessionLocal)

    return {
        "success": True,
        "data": {"id": new_student.id, "name": new_student.name},
        "private_key": priv_rsa,
        "private_key_instruction": "Store this key securely."
    }

# =========================
# GET ALL STUDENTS
# =========================
@router.get("")
def get_students(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    skip = (page - 1) * limit
    total = db.query(Student).count()
    students = db.query(Student).offset(skip).limit(limit).all()

    return {
        "message": "Students fetched successfully",
        "data": [StudentData.model_validate(s) for s in students],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total
        }
    }

# =========================
# GET STUDENT BY ID
# =========================
@router.get("{student_id}", response_model=None)
def get_student(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail={"message": "Student not found"})
    
    return {
        "message": "Student fetched successfully",
        "data": StudentData.model_validate(student)
    }

# =========================
# GET STUDENT BY KTP NUMBER
# =========================
@router.get("ktp/{ktp_number}")
def get_student_by_ktp(ktp_number: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.ktp_number == ktp_number).first()
    
    if not student:
        raise HTTPException(
            status_code=404, 
            detail={"message": f"Student with Identity Number {ktp_number} not found"}
        )
    
    return {
        "message": "Student found successfully",
        "data": StudentData.model_validate(student)
    }

# =========================
# UPDATE STUDENT
# =========================
@router.put("{student_id}")
def update_student(student_id: str, payload: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail={"message": "Student not found"})

    if payload.name:
        student.name = payload.name
    if payload.phone_number:
        student.phone_number = payload.phone_number
    if payload.place_and_date_of_birth:
        student.place_and_date_of_birth = payload.place_and_date_of_birth

    db.commit()
    db.refresh(student)

    return {
        "message": "Student updated successfully",
        "data": StudentData.model_validate(student)
    }

# =========================
# DELETE STUDENT
# =========================
@router.delete("{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail={"message": "Student not found"})

    db.delete(student)
    db.commit()

    return {
        "message": "Student deleted successfully"
    }