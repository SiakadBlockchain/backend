from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from databases.connection import SessionLocal
from models.models import Student, University
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

router = APIRouter()

def generate_student_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
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
    nim: str
    university_id: str


class StudentData(BaseModel):
    id: str
    name: str
    nim: str
    university_id: str
    public_key: str

    class Config:
        from_attributes = True


class ResponseModel(BaseModel):
    message: str
    data: Optional[dict] = None

# =========================
# CREATE STUDENT
# =========================
@router.post("/")
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    existing_student = db.query(Student).filter(Student.nim == student.nim).first()
    if existing_student:
        raise HTTPException(
            status_code=400,
            detail={"message": "NIM already registered"}
        )

    university = db.query(University).filter(University.id == student.university_id).first()
    if not university:
        raise HTTPException(
            status_code=404,
            detail={"message": "University not found"}
        )

    private_key_pem, public_key_pem = generate_student_rsa_keys()

    if len(private_key_pem) < 1600:
         raise HTTPException(status_code=500, detail="Key generation failed: Key too short")

    new_student = Student(
        name=student.name,
        nim=student.nim,
        university_id=student.university_id,
        public_key=public_key_pem.strip(),
        created_at=datetime.utcnow()
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return {
        "message": "Student created successfully with cryptographic identity",
        "data": {
            "student_info": StudentData.model_validate(new_student),
            "cryptography": {
                "private_key": private_key_pem.strip(),
                "note": "Save the private key securely. It will not be stored on the server and cannot be retrieved later."
            }
        }
    }

# =========================
# GET ALL STUDENTS
# =========================

@router.get("/")
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
@router.get("/{student_id}")
def get_student(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail={"message": "Student not found"}
        )

    return {
        "message": "Student fetched successfully",
        "data": StudentData.model_validate(student)
    }

# =========================
# GET STUDENT BY UNIVERSITY ID
# =========================

@router.get("/university/{university_id}")
def get_students_by_university(
    university_id: str,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit

    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(
            status_code=404,
            detail={"message": "University not found"}
        )

    query = db.query(Student).filter(Student.university_id == university_id)

    total = query.count()
    students = query.offset(skip).limit(limit).all()

    return {
        "message": "Students fetched successfully by university",
        "data": [StudentData.model_validate(s) for s in students],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "university_id": university_id
        }
    }


# =========================
# UPDATE STUDENT
# =========================
@router.put("/{student_id}")
def update_student(student_id: str, updated: StudentCreate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail={"message": "Student not found"}
        )

    existing_student = db.query(Student).filter(
        Student.nim == updated.nim,
        Student.id != student_id
    ).first()

    if existing_student:
        raise HTTPException(
            status_code=400,
            detail={"message": "NIM already registered"}
        )

    university = db.query(University).filter(University.id == updated.university_id).first()
    if not university:
        raise HTTPException(
            status_code=404,
            detail={"message": "University not found"}
        )

    student.name = updated.name
    student.nim = updated.nim
    student.university_id = updated.university_id

    db.commit()
    db.refresh(student)

    return {
        "message": "Student updated successfully",
        "data": StudentData.model_validate(student)
    }


# =========================
# DELETE STUDENT
# =========================
@router.delete("/{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail={"message": "Student not found"}
        )

    db.delete(student)
    db.commit()

    return {
        "message": "Student deleted successfully"
    }