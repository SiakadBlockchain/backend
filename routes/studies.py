from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from databases.connection import SessionLocal
from .diplomas import DiplomaData
from models.models import Student, University, Study
from typing import Optional, List
from pydantic import BaseModel

from routes.universities import UniversityData

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
class StudyBase(BaseModel):
    student_id: str
    university_id: str
    major: str
    level: str
    nim: str
    diplomas: List[DiplomaData] = []
    university: Optional[UniversityData] = None

    class Config:
        from_attributes = True

class StudyCreate(StudyBase):
    pass

class StudyData(StudyBase):
    id: str

    class Config:
        from_attributes = True

# =========================
# CREATE STUDY
# =========================
@router.post("/")
def create_study(study: StudyCreate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == study.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail={"message": "Student not found"})

    university = db.query(University).filter(University.id == study.university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail={"message": "University not found"})

    existing_nim = db.query(Study).filter(Study.nim == study.nim).first()
    if existing_nim:
        raise HTTPException(status_code=400, detail={"message": "NIM already registered in studies"})

    new_study = Study(
        student_id=study.student_id,
        university_id=study.university_id,
        major=study.major,
        level=study.level,
        nim=study.nim
    )

    db.add(new_study)
    db.commit()
    db.refresh(new_study)

    return {
        "message": "Study record created successfully",
        "data": StudyData.model_validate(new_study)
    }

# =========================
# GET ALL STUDIES
# =========================
@router.get("/")
def get_studies(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    skip = (page - 1) * limit
    total = db.query(Study).count()
    studies = db.query(Study).offset(skip).limit(limit).all()

    return {
        "message": "Studies fetched successfully",
        "data": [StudyData.model_validate(s) for s in studies],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total
        }
    }

# =========================
# GET STUDY BY ID
# =========================
@router.get("/{study_id}")
def get_study(study_id: str, db: Session = Depends(get_db)):
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail={"message": "Study record not found"})

    return {
        "message": "Study fetched successfully",
        "data": StudyData.model_validate(study)
    }

# =========================
# GET STUDY BY NIM
# =========================
@router.get("/nim/{nim}")
def get_study_by_nim(nim: str, db: Session = Depends(get_db)):
    study = db.query(Study).filter(Study.nim == nim).first()
    if not study:
        raise HTTPException(status_code=404, detail={"message": "Study record not found"})

    return {
        "message": "Study fetched successfully",
        "data": StudyData.model_validate(study)
    }

# =========================
# GET STUDY BY STUDENT ID
# =========================
@router.get("/student/{student_id}")
def get_study_by_student_id(student_id: str, db: Session = Depends(get_db)):
    studies = db.query(Study)\
                .options(joinedload(Study.diplomas))\
                .options(joinedload(Study.university))\
                .filter(Study.student_id == student_id)\
                .all()
    
    if not studies:
        return {
            "message": "No study records found",
            "data": []
        }

    return {
        "message": "Studies fetched successfully",
        "data": [StudyData.model_validate(s) for s in studies]
    }

# =========================
# GET BY UNIVERSITY ID
# =========================
@router.get("/university/{university_id}")
def get_studies_by_university(
    university_id: str, 
    page: int = 1, 
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    
    query = db.query(Study).filter(Study.university_id == university_id)
    total = query.count()
    studies = query.offset(skip).limit(limit).all()

    return {
        "message": "Studies fetched successfully by university",
        "data": [StudyData.model_validate(s) for s in studies],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "university_id": university_id
        }
    }

# =========================
# UPDATE STUDY
# =========================
@router.put("/{study_id}")
def update_study(study_id: str, updated: StudyCreate, db: Session = Depends(get_db)):
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail={"message": "Study record not found"})

    existing_nim = db.query(Study).filter(
        Study.nim == updated.nim, 
        Study.id != study_id
    ).first()
    if existing_nim:
        raise HTTPException(status_code=400, detail={"message": "NIM already registered in another record"})

    study.student_id = updated.student_id
    study.university_id = updated.university_id
    study.major = updated.major
    study.level = updated.level
    study.nim = updated.nim

    db.commit()
    db.refresh(study)

    return {
        "message": "Study record updated successfully",
        "data": StudyData.model_validate(study)
    }

# =========================
# DELETE STUDY
# =========================
@router.delete("/{study_id}")
def delete_study(study_id: str, db: Session = Depends(get_db)):
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail={"message": "Study record not found"})

    db.delete(study)
    db.commit()

    return {
        "message": "Study record deleted successfully"
    }