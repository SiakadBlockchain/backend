import os
import json
import hashlib
import requests
import io
import uuid

from fastapi import APIRouter, HTTPException, Depends, Path, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from web3 import Web3
from dotenv import load_dotenv
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.backends import default_backend

from databases.connection import SessionLocal
from models.models import Diploma, Student, University, Transaction, Study, Wallet

from cryptography.fernet import Fernet

load_dotenv()

MASTER_KEY = os.getenv("MASTER_KEY")
if not MASTER_KEY:
    raise ValueError("MASTER_KEY not found in environment variables")
cipher_suite = Fernet(MASTER_KEY.encode())

RPC_URL = os.getenv("RPC_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_SECRET_API_KEY = os.getenv("PINATA_SECRET_API_KEY")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

with open("abis/DiplomaStorage.json", "r") as f:
    contract_abi = json.load(f)["abi"]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_sha256(file_content: bytes) -> str:
    return hashlib.sha256(file_content).hexdigest()

async def upload_to_pinata(file_content: bytes, filename: str) -> str:
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_API_KEY
    }
    files = {"file": (filename, file_content)}
    try:
        response = requests.post(url, files=files, headers=headers)
        response.raise_for_status()
        return response.json()["IpfsHash"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to Pinata: {str(e)}")

def encrypt_pdf_hybrid(pdf_content: bytes, public_key_pem: str):
    aes_key = os.urandom(32)
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(pdf_content) + padder.finalize()
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext_pdf = encryptor.update(padded_data) + encryptor.finalize()
    public_key = serialization.load_pem_public_key(public_key_pem.encode(), backend=default_backend())
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return ciphertext_pdf, encrypted_aes_key, iv

def decrypt_pdf_hybrid(ciphertext_pdf: bytes, encrypted_aes_key_hex: str, iv_hex: str, private_key_pem: str):
    lines = [line.strip() for line in private_key_pem.splitlines() if line.strip()]
    base64_parts = [line for line in lines if "-----BEGIN" not in line and "-----END" not in line]
    all_data = "".join(base64_parts).replace(" ", "")
    formatted_data = "\n".join([all_data[i:i+64] for i in range(0, len(all_data), 64)])
    final_pem = "-----BEGIN PRIVATE KEY-----\n" + formatted_data + "\n-----END PRIVATE KEY-----"
    private_key = serialization.load_pem_private_key(final_pem.encode('utf-8'), password=None, backend=default_backend())
    aes_key = private_key.decrypt(
        bytes.fromhex(encrypted_aes_key_hex.strip()),
        asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(bytes.fromhex(iv_hex.strip())), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext_pdf) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()

# =========================
# SCHEMA
# =========================

class DiplomaUpdate(BaseModel):
    diploma_number: str
    graduationYear: str
    studies_id: str
    ipfs_cid: Optional[str] = None
    document_hash: str
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    status: str

class DiplomaData(BaseModel):
    id: str
    studies_id: str
    student_id: str
    university_id: str
    graduationYear: str
    diploma_number: str
    document_hash: str
    ipfs_cid: Optional[str] = None
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    status: str
    issued_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# =========================
# CREATE DIPLOMA
# =========================

@router.post("")
async def create_diploma(
    studies_id: str = Form(...),
    graduationYear: str = Form(...),
    diploma_number: str = Form(...),
    file: UploadFile = File(...),
    univ_key_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    study = db.query(Study).filter(Study.id == studies_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study record not found")

    from models.models import User 
    univ_user = db.query(User).filter(
        User.university_id == study.university_id,
        User.role == "university"
    ).first()

    if not univ_user or not univ_user.public_key:
        raise HTTPException(status_code=404, detail="University administrator account or public key not found")

    existing_diploma = db.query(Diploma).filter(Diploma.studies_id == studies_id).first()
    if existing_diploma:
        raise HTTPException(status_code=400, detail="Diploma already issued for this study record")

    student = db.query(Student).filter(Student.id == study.student_id).first()
    if not student or not student.public_key:
        raise HTTPException(status_code=404, detail="Student or Student Public Key not found")

    content = await file.read()
    doc_hash = calculate_sha256(content)

    try:
        univ_key_bytes = await univ_key_file.read()
        univ_private_key = serialization.load_pem_private_key(
            univ_key_bytes,
            password=None,
            backend=default_backend()
        )

        derived_public_key = univ_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode().strip()

        if derived_public_key != univ_user.public_key.strip():
            raise HTTPException(
                status_code=401, 
                detail="The uploaded private key does not belong to this university's authorized account."
            )

        univ_private_key.sign(
            doc_hash.encode(),
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"University signature/validation failed: {str(e)}")

    try:
        ciphertext_pdf, encrypted_key, iv = encrypt_pdf_hybrid(content, student.public_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")

    generated_ipfs_cid = await upload_to_pinata(ciphertext_pdf, f"encrypted_{file.filename}")

    diploma_id = str(uuid.uuid4())
    new_diploma = Diploma(
        id=diploma_id,
        studies_id=studies_id,
        student_id=study.student_id,
        university_id=study.university_id,
        graduationYear=graduationYear,
        diploma_number=diploma_number,
        ipfs_cid=generated_ipfs_cid,
        document_hash=doc_hash,
        encrypted_key=encrypted_key.hex(),
        iv=iv.hex(),
        status="pending",
        issued_at=datetime.utcnow()
    )
    db.add(new_diploma)

    new_tx = Transaction(
        id=str(uuid.uuid4()),
        reference_id=diploma_id,
        tx_type='ISSUE_DIPLOMA',
        status='pending',
        created_at=datetime.utcnow()
    )
    db.add(new_tx)
    db.commit()

    return {
        "message": "Diploma validated, signed by university, encrypted, and uploaded to IPFS.",
        "diploma_id": diploma_id,
        "ipfs_cid": generated_ipfs_cid,
        "document_hash": doc_hash
    }

# =========================
# GET DIPLOMAS
# =========================

@router.get("")
def get_diplomas(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    skip = (page - 1) * limit
    total = db.query(Diploma).count()
    diplomas = db.query(Diploma).offset(skip).limit(limit).all()

    return {
        "message": "Diplomas fetched successfully",
        "data": [DiplomaData.model_validate(d) for d in diplomas],
        "meta": {"page": page, "limit": limit, "total": total}
    }

@router.get("{diploma_id}")
def get_diploma(diploma_id: str, db: Session = Depends(get_db)):
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(status_code=404, detail="Diploma not found")

    return {
        "message": "Diploma fetched successfully",
        "data": DiplomaData.model_validate(diploma)
    }

@router.get("university/{university_id}")
def fetch_diplomas_by_university(
    university_id: str, 
    page: int = 1, 
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    query = db.query(Diploma).join(Study).filter(Study.university_id == university_id)
    
    total = query.count()
    diplomas = query.offset(skip).limit(limit).all()

    return {
        "message": f"Diplomas for university {university_id} fetched successfully",
        "data": [DiplomaData.model_validate(d) for d in diplomas],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total
        }
    }

# =========================
# UPDATE & DELETE
# =========================

@router.put("{diploma_id}")
def update_diploma(diploma_id: str, updated: DiplomaUpdate, db: Session = Depends(get_db)):
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(status_code=404, detail="Diploma not found")

    diploma.diploma_number = updated.diploma_number
    diploma.graduationYear = updated.graduationYear
    diploma.studies_id = updated.studies_id
    diploma.ipfs_cid = updated.ipfs_cid
    diploma.document_hash = updated.document_hash
    diploma.tx_hash = updated.tx_hash
    diploma.block_number = updated.block_number
    diploma.status = updated.status

    db.commit()
    db.refresh(diploma)

    return {
        "message": "Diploma updated successfully",
        "data": DiplomaData.model_validate(diploma)
    }

@router.delete("{diploma_id}")
def delete_diploma(diploma_id: str, db: Session = Depends(get_db)):
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(status_code=404, detail="Diploma not found")
    db.delete(diploma)
    db.commit()
    return {"message": "Diploma deleted successfully"}

# =========================
# VERIFICATION & DOWNLOAD
# =========================

@router.get("verify-on-chain/{doc_hash}")
def verify_on_chain(doc_hash: str):
    try:
        on_chain_data = contract.functions.getDiploma(doc_hash).call()
        if not on_chain_data[0]:
            raise HTTPException(status_code=404, detail="Data not found on blockchain")

        return {
            "source": "blockchain",
            "is_valid": on_chain_data[6] == 0,
            "data": {
                "diploma_number": on_chain_data[3],
                "ipfs_cid": on_chain_data[4],
                "status": "valid" if on_chain_data[6] == 0 else "revoked",
                "issued_at_timestamp": on_chain_data[7]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("{diploma_id}/verify-and-download")
async def verify_and_download_diploma(diploma_id: str, db: Session = Depends(get_db)):
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(status_code=404, detail="Diploma data not found")

    student = db.query(Student).filter(Student.id == diploma.student_id).first()
    if not student or not student.rsa_private_key_encrypted:
        raise HTTPException(status_code=404, detail="RSA decryption key not found")

    try:
        decrypted_rsa_pem = cipher_suite.decrypt(student.rsa_private_key_encrypted.encode()).decode('utf-8')
        
        ipfs_url = f"https://gateway.pinata.cloud/ipfs/{diploma.ipfs_cid}"
        res = requests.get(ipfs_url, timeout=30)
        res.raise_for_status()
        
        decrypted_pdf = decrypt_pdf_hybrid(
            res.content,
            diploma.encrypted_key,
            diploma.iv,
            decrypted_rsa_pem
        )

        if calculate_sha256(decrypted_pdf) != diploma.document_hash:
            raise HTTPException(status_code=400, detail="File integrity compromised")

        return StreamingResponse(
            io.BytesIO(decrypted_pdf),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Diploma_{diploma.diploma_number}.pdf"}
        )

    except Exception as e:
        print(f"FAILED: {str(e)}")
        raise HTTPException(status_code=401, detail="Failed to decrypt diploma")