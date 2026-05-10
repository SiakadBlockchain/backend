import asyncio
from sqlalchemy.orm import Session
from models.models import Student

async def auto_cleanup_otp(student_id: int, db_session_factory):
    """Menghapus kode OTP secara otomatis setelah 60 detik."""
    await asyncio.sleep(60)
    
    db = db_session_factory()
    try:
        student = db.query(Student).filter(Student.id == student_id).first()
        if student and student.otp_secret:
            student.otp_secret = None
            db.commit()
    finally:
        db.close()