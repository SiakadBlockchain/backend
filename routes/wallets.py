from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from databases.connection import SessionLocal
from models.models import Wallet, User
from typing import Optional
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
class WalletCreate(BaseModel):
    user_id: str
    wallet_address: str
    is_primary: bool = False
    verified: bool = False


class WalletUpdate(BaseModel):
    wallet_address: str
    is_primary: bool
    verified: bool


class WalletData(BaseModel):
    id: str
    user_id: str
    wallet_address: str
    is_primary: bool
    verified: bool

    class Config:
        from_attributes = True


class ResponseModel(BaseModel):
    message: str
    data: Optional[dict] = None


# =========================
# CREATE WALLET
# =========================
@router.post("/")
def create_wallet(wallet: WalletCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == wallet.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"message": "User not found"}
        )

    existing_wallet = db.query(Wallet).filter(
        Wallet.wallet_address == wallet.wallet_address
    ).first()

    if existing_wallet:
        raise HTTPException(
            status_code=400,
            detail={"message": "Wallet address already exists"}
        )

    if wallet.is_primary:
        db.query(Wallet).filter(
            Wallet.user_id == wallet.user_id
        ).update({"is_primary": False})

    new_wallet = Wallet(
        user_id=wallet.user_id,
        wallet_address=wallet.wallet_address,
        is_primary=wallet.is_primary,
        verified=wallet.verified,
        created_at=datetime.utcnow()
    )

    db.add(new_wallet)
    db.commit()
    db.refresh(new_wallet)

    return {
        "message": "Wallet created successfully",
        "data": WalletData.model_validate(new_wallet)
    }


# =========================
# GET ALL WALLETS
# =========================
@router.get("/")
def get_wallets(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    skip = (page - 1) * limit

    total = db.query(Wallet).count()
    wallets = db.query(Wallet).offset(skip).limit(limit).all()

    return {
        "message": "Wallets fetched successfully",
        "data": [WalletData.model_validate(w) for w in wallets],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total
        }
    }

# =========================
# GET WALLET BY ID
# =========================
@router.get("/{wallet_id}")
def get_wallet(wallet_id: str, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail={"message": "Wallet not found"}
        )

    return {
        "message": "Wallet fetched successfully",
        "data": WalletData.model_validate(wallet)
    }

# =========================
# UPDATE WALLET
# =========================
@router.put("/{wallet_id}")
def update_wallet(wallet_id: str, updated: WalletUpdate, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail={"message": "Wallet not found"}
        )

    existing_wallet = db.query(Wallet).filter(
        Wallet.wallet_address == updated.wallet_address,
        Wallet.id != wallet_id
    ).first()

    if existing_wallet:
        raise HTTPException(
            status_code=400,
            detail={"message": "Wallet address already exists"}
        )
    
    if updated.is_primary:
        db.query(Wallet).filter(
            Wallet.user_id == wallet.user_id
        ).update({"is_primary": False})

    wallet.wallet_address = updated.wallet_address
    wallet.is_primary = updated.is_primary
    wallet.verified = updated.verified

    db.commit()
    db.refresh(wallet)

    return {
        "message": "Wallet updated successfully",
        "data": WalletData.model_validate(wallet)
    }


# =========================
# DELETE WALLET
# =========================
@router.delete("/{wallet_id}")
def delete_wallet(wallet_id: str, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail={"message": "Wallet not found"}
        )

    db.delete(wallet)
    db.commit()

    return {
        "message": "Wallet deleted successfully"
    }