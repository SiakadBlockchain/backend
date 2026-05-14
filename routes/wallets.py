import os
import random
from datetime import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from cryptography.fernet import Fernet
from eth_account import Account
from web3 import Web3

from databases.connection import SessionLocal
from models.models import Student, Wallet
from .utils.helpers import auto_cleanup_otp

router = APIRouter()
load_dotenv()

# =========================
# CONFIG & SECURITY
# =========================
AVAX_RPC_URL = os.getenv("RPC_URL")
w3 = Web3(Web3.HTTPProvider(AVAX_RPC_URL))

MASTER_KEY = os.getenv("MASTER_KEY")
if not MASTER_KEY:
    raise ValueError("MASTER_KEY not found in environment variables")
cipher_suite = Fernet(MASTER_KEY.encode())

Account.enable_unaudited_hdwallet_features()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# SCHEMA
# =========================
class OTPVerification(BaseModel):
    student_id: str
    otp_code: str

class WalletResponse(BaseModel):
    student_id: str
    blockchain_address: str
    is_connected: bool
    
    class Config:
        from_attributes = True

class ConnectionUpdate(BaseModel):
    is_connected: bool

class OTPRequest(BaseModel):
    student_id: str

def create_wallet_logic(student_id: str, db: Session):
    existing_wallet = db.query(Wallet).filter(Wallet.student_id == student_id).first()
    if existing_wallet:
        return existing_wallet

    acct = Account.create()
    address = acct.address

    new_wallet = Wallet(
        student_id=student_id,
        blockchain_address=address,
        is_connected=True,
        created_at=datetime.utcnow()
    )
    
    db.add(new_wallet)
    return new_wallet

def generate_otp_code(length: int = 6) -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

def send_otp_to_console(phone_number: str, otp_code: str):
    print("\n" + "="*50)
    print(" [SIAKADCHAIN DEBUG - OTP VERIFICATION]")
    print(f" TARGET NUMBER : {phone_number}")
    print(f" OTP CODE      : {otp_code}")
    print("="*50 + "\n")
    return True

# =========================
# REQUEST NEW OTP
# =========================

@router.post("otp-request")
def request_new_otp(
    payload: OTPRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    new_otp = generate_otp_code()
    
    student.otp_secret = new_otp
    db.commit()
    db.refresh(student)

    send_otp_to_console(student.phone_number, new_otp)

    background_tasks.add_task(auto_cleanup_otp, student.id, SessionLocal)

    return {
        "status": "success",
        "message": f"A new OTP code has been sent to {student.phone_number[:4]}****"
    }

# =========================
# VERIFY OTP
# =========================

@router.post("verify-otp")
def verify_otp_and_activate(payload: OTPVerification, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not student.otp_secret or student.otp_secret != payload.otp_code:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code")

    try:
        wallet = create_wallet_logic(student.id, db)
        
        student.is_phone_verified = True 
        student.otp_secret = None
        
        db.commit()
        db.refresh(student)
        
        return {
            "status": "success",
            "message": "Verification successful and wallet has been activated",
            "data": {
                "student_name": student.name,
                "avax_address": wallet.blockchain_address
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Automatic wallet activation failed: {str(e)}")

# =========================
# DELETE WALLET
# =========================

@router.delete("remove/{student_id}")
def delete_wallet(student_id: str, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.student_id == student_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    db.delete(wallet)
    db.commit()
    return {"message": "Wallet successfully removed from the system"}