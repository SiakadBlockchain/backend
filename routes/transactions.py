import os
import json

from web3 import Web3
from dotenv import load_dotenv

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from databases.connection import SessionLocal
from models.models import Transaction, Diploma
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter()

RPC_URL = os.getenv("RPC_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

with open("abis/DiplomaStorage.json", "r") as f:
    contract_abi = json.load(f)["abi"]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# SCHEMA
# =========================
class TransactionData(BaseModel):
    id: str
    tx_hash: Optional[str] = None
    reference_id: str
    tx_type: str
    wallet_address: str
    status: str
    block_number: Optional[int] = None
    gas_used: Optional[int] = None

    class Config:
        from_attributes = True

class ResponseModel(BaseModel):
    message: str
    data: Optional[dict] = None

# =========================
# GET ALL TRANSACTIONS
# =========================
@router.get("/")
def get_transactions(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    try:
        skip = (page - 1) * limit

        total = db.query(Transaction).count()
        transactions = db.query(Transaction)\
            .order_by(Transaction.id.desc())\
            .offset(skip).limit(limit).all()

        validated_data = [TransactionData.model_validate(t) for t in transactions]

        return {
            "message": "Transactions fetched successfully",
            "data": validated_data,
            "meta": {
                "page": page,
                "limit": limit,
                "total": total
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# =========================
# GET TRANSACTION BY ID
# =========================
@router.get("/{transaction_id}")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail={"message": "Transaction not found"}
        )

    return {
        "message": "Transaction fetched successfully",
        "data": TransactionData.model_validate(transaction)
    }

@router.post("/{transaction_id}/approve")
async def approve_transaction(transaction_id: str, db: Session = Depends(get_db)):
    tx_record = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx_record or tx_record.status != 'pending':
        raise HTTPException(status_code=404, detail="Pending transaction not found")
    diploma = db.query(Diploma).filter(Diploma.id == tx_record.reference_id).first()
    try:
        issued_at_ts = int(diploma.issued_at.timestamp())
        nonce = w3.eth.get_transaction_count(account.address)
        
        tx = contract.functions.tambahIjazah(
            diploma.id,
            diploma.student_id,
            diploma.university_id,
            diploma.diploma_number,
            diploma.ipfs_cid or "",
            diploma.document_hash,
            issued_at_ts
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'gas': 500000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        tx_record.status = 'success'
        tx_record.tx_hash = tx_hash.hex()
        tx_record.block_number = tx_receipt.blockNumber
        tx_record.gas_used = tx_receipt.gasUsed
        diploma.status = 'valid'
        diploma.tx_hash = tx_hash.hex()
        diploma.block_number = tx_receipt.blockNumber

        db.commit()
        return {"message": "Transaction approved and anchored to blockchain"}

    except Exception as e:
        tx_record.status = 'failed'
        db.commit()
        raise HTTPException(status_code=500, detail=f"Approval Failed: {str(e)}")