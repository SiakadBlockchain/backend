from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from databases.connection import SessionLocal
from models.models import University
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# SCHEMA
# =========================
class UniversityCreate(BaseModel):
    name: str
    accreditation: str

class UniversityData(BaseModel):
    id: str
    name: str
    accreditation: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

# =========================
# CREATE UNIVERSITY
# =========================
@router.post("")
def create_university(university: UniversityCreate, db: Session = Depends(get_db)):
    if university.accreditation not in ['A', 'B', 'C']:
        raise HTTPException(
            status_code=400, 
            detail={"message": "Accreditation must be A, B, or C"}
        )

    new_university = University(
        name=university.name,
        accreditation=university.accreditation,
        created_at=datetime.utcnow()
    )

    db.add(new_university)
    db.commit()
    db.refresh(new_university)

    return {
        "message": "University created successfully",
        "data": UniversityData.model_validate(new_university)
    }

# =========================
# GET ALL UNIVERSITIES
# =========================
@router.get("")
def get_universities(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    skip = (page - 1) * limit

    total = db.query(University).count()
    universities = db.query(University).offset(skip).limit(limit).all()

    return {
        "message": "Universities fetched successfully",
        "data": [UniversityData.model_validate(u) for u in universities],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total
        }
    }

# =========================
# GET UNIVERSITY BY ID
# =========================
@router.get("{university_id}")
def get_university(university_id: str, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.id == university_id).first()

    if not university:
        raise HTTPException(
            status_code=404,
            detail={"message": "University not found"}
        )

    return {
        "message": "University fetched successfully",
        "data": UniversityData.model_validate(university)
    }

# =========================
# UPDATE UNIVERSITY
# =========================
@router.put("{university_id}")
def update_university(university_id: str, updated: UniversityCreate, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.id == university_id).first()

    if not university:
        raise HTTPException(
            status_code=404,
            detail={"message": "University not found"}
        )

    if updated.accreditation not in ['A', 'B', 'C']:
        raise HTTPException(
            status_code=400, 
            detail={"message": "Accreditation must be A, B, or C"}
        )

    university.name = updated.name
    university.accreditation = updated.accreditation

    db.commit()
    db.refresh(university)

    return {
        "message": "University updated successfully",
        "data": UniversityData.model_validate(university)
    }

# =========================
# DELETE UNIVERSITY
# =========================
@router.delete("{university_id}")
def delete_university(university_id: str, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.id == university_id).first()

    if not university:
        raise HTTPException(
            status_code=404,
            detail={"message": "University not found"}
        )

    db.delete(university)
    db.commit()

    return {
        "message": "University deleted successfully"
    }