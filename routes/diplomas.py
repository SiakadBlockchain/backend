import os
import json
import hashlib
import requests
import io

from fastapi.responses import StreamingResponse
from web3 import Web3
from dotenv import load_dotenv

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from databases.connection import SessionLocal
from models.models import Diploma, Student, University, Transaction
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.backends import default_backend

load_dotenv()

# Konfigurasi Web3

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

# =========================

router = APIRouter()

def calculate_sha256(file_content: bytes) -> str:
    return hashlib.sha256(file_content).hexdigest()

async def upload_to_pinata(file_content: bytes, filename: str) -> str:
    """Mengunggah konten file ke Pinata IPFS dan mengembalikan CID."""
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    
    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_API_KEY
    }
    
    files = {
        "file": (filename, file_content)
    }

    try:
        response = requests.post(url, files=files, headers=headers)
        response.raise_for_status() # Akan memicu error jika status code bukan 2xx
        result = response.json()
        return result["IpfsHash"]
    except Exception as e:
        # Kita raise HTTPException agar client tahu ada masalah di sisi IPFS
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to upload to Pinata: {str(e)}"
        )
    
def encrypt_pdf_hybrid(pdf_content: bytes, public_key_pem: str):
    """
    Mengenkripsi PDF menggunakan AES-256, lalu mengenkripsi kunci AES dengan RSA.
    Mengembalikan (ciphertext_pdf, encrypted_aes_key, iv)
    """
    # 1. Generate kunci simetris AES-256 dan IV (Initialization Vector)
    aes_key = os.urandom(32)
    iv = os.urandom(16)

    # 2. Padding PDF agar sesuai dengan ukuran block AES
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(pdf_content) + padder.finalize()

    # 3. Enkripsi PDF dengan AES
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext_pdf = encryptor.update(padded_data) + encryptor.finalize()

    # 4. Enkripsi kunci AES dengan RSA Public Key Mahasiswa
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

import base64

def decrypt_pdf_hybrid(ciphertext_pdf: bytes, encrypted_aes_key_hex: str, iv_hex: str, private_key_pem: str):
    try:
        # --- TAHAP REKONSTRUKSI TOTAL (Mencegah InvalidLength) ---
        # 1. Ambil semua teks, bersihkan dari whitespace
        lines = [line.strip() for line in private_key_pem.splitlines() if line.strip()]
        
        # 2. Ambil hanya data base64 (yang ada di antara header dan footer)
        base64_parts = []
        for line in lines:
            if "-----BEGIN" in line or "-----END" in line:
                continue
            base64_parts.append(line)
        
        # 3. Gabung semua menjadi satu string tanpa spasi/newline sama sekali
        all_data = "".join(base64_parts).replace(" ", "")
        
        # 4. Susun ulang ke format PEM standar: 64 karakter per baris
        # Ini penting agar library cryptography tidak bingung menghitung offset
        formatted_data = "\n".join([all_data[i:i+64] for i in range(0, len(all_data), 64)])
        
        final_pem = (
            "-----BEGIN PRIVATE KEY-----\n" +
            formatted_data +
            "\n-----END PRIVATE KEY-----"
        )

        # --- LOADING KUNCI ---
        private_key = serialization.load_pem_private_key(
            final_pem.encode('utf-8'),
            password=None,
            backend=default_backend()
        )

        # --- DEKRIPSI RSA (Membuka Kunci AES) ---
        encrypted_aes_key = bytes.fromhex(encrypted_aes_key_hex.strip())
        aes_key = private_key.decrypt(
            encrypted_aes_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # --- DEKRIPSI AES (Membuka File PDF) ---
        iv = bytes.fromhex(iv_hex.strip())
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        padded_data = decryptor.update(ciphertext_pdf) + decryptor.finalize()
        
        # Remove Padding PKCS7
        unpadder = padding.PKCS7(128).unpadder()
        pdf_content = unpadder.update(padded_data) + unpadder.finalize()

        return pdf_content

    except Exception as e:
        print(f"DEBUG KRIPTOGRAFI: {type(e).__name__} - {str(e)}")
        raise e

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# SCHEMA
# =========================
class DiplomaCreate(BaseModel):
    student_id: str
    university_id: str
    diploma_number: str
    ipfs_cid: Optional[str] = None
    document_hash: str
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None


class DiplomaUpdate(BaseModel):
    diploma_number: str
    ipfs_cid: Optional[str] = None
    document_hash: str
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    status: str  # valid / revoked

class DiplomaVerify(BaseModel):
    document_hash: str

class DiplomaData(BaseModel):
    id: str
    student_id: str
    university_id: str
    diploma_number: str
    document_hash: str
    ipfs_cid: Optional[str] = None
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    status: str

    class Config:
        from_attributes = True

# =========================
# CREATE ISSUE DIPLOMA
# =========================
@router.post("/")
async def create_diploma(
    student_id: str = Form(...),
    university_id: str = Form(...),
    diploma_number: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Validasi File & Baca Konten
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    content = await file.read()
    
    # 2. Hashing PDF asli (Plaintext) untuk integritas di Blockchain
    doc_hash = calculate_sha256(content)

    # 3. Ambil Public Key Mahasiswa dari DB
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student or not student.public_key:
        raise HTTPException(status_code=404, detail="Student or Student Public Key not found")

    # 4. Proses Enkripsi Hibrida
    try:
        ciphertext_pdf, encrypted_key, iv = encrypt_pdf_hybrid(content, student.public_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")

    # 5. Upload Ciphertext PDF ke Pinata IPFS
    # Note: Yang diunggah adalah ciphertext_pdf, bukan content asli
    generated_ipfs_cid = await upload_to_pinata(ciphertext_pdf, f"encrypted_{file.filename}")

    # 6. Simpan ke Database
    import uuid
    diploma_id = str(uuid.uuid4())
    
    new_diploma = Diploma(
        id=diploma_id,
        student_id=student_id,
        university_id=university_id,
        diploma_number=diploma_number,
        ipfs_cid=generated_ipfs_cid,
        document_hash=doc_hash, # Tetap simpan hash asli untuk verifikasi nanti
        # Simpan metadata enkripsi agar bisa didekripsi nantinya
        encrypted_key=encrypted_key.hex(), 
        iv=iv.hex(),
        status="pending",
        issued_at=datetime.utcnow()
    )
    db.add(new_diploma)

    # 7. Record Transaksi
    new_tx = Transaction(
        id=str(uuid.uuid4()),
        reference_id=diploma_id,
        tx_type='ISSUE_DIPLOMA',
        status='pending',
        wallet_address=account.address,
        created_at=datetime.utcnow()
    )
    db.add(new_tx)
    
    db.commit()

    return {
        "message": "Diploma encrypted and uploaded to IPFS. Waiting for approval.",
        "diploma_id": diploma_id,
        "ipfs_cid": generated_ipfs_cid,
        "document_hash": doc_hash,
        "transaction_id": new_tx.id
    }

# =========================
# GET ALL DIPLOMAS
# =========================
@router.get("/")
def get_diplomas(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    skip = (page - 1) * limit

    total = db.query(Diploma).count()
    diplomas = db.query(Diploma).offset(skip).limit(limit).all()

    return {
        "message": "Diplomas fetched successfully",
        "data": [DiplomaData.model_validate(d) for d in diplomas],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total
        }
    }


# =========================
# GET DIPLOMA BY ID
# =========================
@router.get("/{diploma_id}")
def get_diploma(diploma_id: str, db: Session = Depends(get_db)):
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()

    if not diploma:
        raise HTTPException(
            status_code=404,
            detail={"message": "Diploma not found"}
        )

    return {
        "message": "Diploma fetched successfully",
        "data": DiplomaData.model_validate(diploma)
    }

# =========================
# GET DIPLOMAS BY UNIVERSITY ID
# =========================

@router.get("/university/{university_id}")
def get_diplomas_by_university(
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
    
    query = db.query(Diploma).filter(Diploma.university_id == university_id)

    total = query.count()
    diplomas = query.offset(skip).limit(limit).all()

    return {
        "message": "Diplomas fetched successfully by university",
        "data": [DiplomaData.model_validate(d) for d in diplomas],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "university_id": university_id
        }
    }

# =========================
# UPDATE DIPLOMA
# =========================
@router.put("/{diploma_id}")
def update_diploma(diploma_id: str, updated: DiplomaUpdate, db: Session = Depends(get_db)):
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()

    if not diploma:
        raise HTTPException(
            status_code=404,
            detail={"message": "Diploma not found"}
        )

    diploma.diploma_number = updated.diploma_number
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


# =========================
# DELETE DIPLOMA
# =========================
@router.delete("/{diploma_id}")
def delete_diploma(diploma_id: str, db: Session = Depends(get_db)):
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()

    if not diploma:
        raise HTTPException(
            status_code=404,
            detail={"message": "Diploma not found"}
        )

    db.delete(diploma)
    db.commit()

    return {
        "message": "Diploma deleted successfully",
        "data": None
    }

# =========================
# REVOKE DIPLOMA
# =========================
@router.post("/{diploma_id}/revoke")
def revoke_diploma(diploma_id: str, db: Session = Depends(get_db)):
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()

    if not diploma:
        raise HTTPException(status_code=404, detail="Diploma not found")

    if diploma.status == "revoked":
        raise HTTPException(status_code=400, detail="Diploma already revoked")

    # 1. Update di Blockchain
    try:
        nonce = w3.eth.get_transaction_count(account.address)
        # Status Revoked di Enum Smart Contract adalah 1
        tx = contract.functions.updateStatus(diploma.document_hash, 1).build_transaction({
            'chainId': w3.eth.chain_id,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke on blockchain: {str(e)}")

    # 2. Update di Database
    diploma.status = "revoked"
    db.commit()
    db.refresh(diploma)

    return {
        "message": "Diploma revoked successfully on DB and Blockchain",
        "tx_hash": tx_hash.hex(),
        "data": DiplomaData.model_validate(diploma)
    }


# =========================
# VERIFY ON BLOCKCHAIN (NEW ENDPOINT)
# =========================
@router.get("/verify-on-chain/{doc_hash}")
def verify_on_chain(doc_hash: str):
    """Mengecek langsung ke smart contract apakah data ada dan valid"""
    try:
        on_chain_data = contract.functions.getDiploma(doc_hash).call()
        
        # on_chain_data mengembalikan tuple sesuai struktur Struct di Solidity
        # [id, studentId, universityId, diplomaNumber, ipfsCid, documentHash, status, issuedAt]
        
        if not on_chain_data[0]: # Jika ID kosong
            raise HTTPException(status_code=404, detail="Data not found on blockchain")

        return {
            "source": "blockchain",
            "is_valid": on_chain_data[6] == 0, # Status.Valid = 0
            "data": {
                "diploma_number": on_chain_data[3],
                "ipfs_cid": on_chain_data[4],
                "status": "valid" if on_chain_data[6] == 0 else "revoked",
                "issued_at_timestamp": on_chain_data[7]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{diploma_id}/verify-and-download")
async def verify_and_download(
    diploma_id: str,
    key_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Cari data ijazah di Database
    diploma = db.query(Diploma).filter(Diploma.id == diploma_id).first()
    if not diploma:
        raise HTTPException(status_code=404, detail="Diploma record not found")
    
    if diploma.status != "valid":
        raise HTTPException(status_code=400, detail="Diploma is not yet validated on blockchain")

    # 2. Baca Private Key dengan pembersihan string yang lebih ketat
    try:
        raw_key_bytes = await key_file.read()
        # Gunakan decode 'utf-8' saja tanpa strip agresif di sini
        private_key_string = raw_key_bytes.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail="Gagal membaca file kunci")

    # 3. Ambil Ciphertext dari IPFS
    ipfs_url = f"https://gateway.pinata.cloud/ipfs/{diploma.ipfs_cid}"
    try:
        response = requests.get(ipfs_url, timeout=30) # Tambahkan timeout
        if response.status_code != 200:
            raise Exception(f"IPFS Gateway returned status {response.status_code}")
        ciphertext_pdf = response.content
    except Exception as e:
        print(f"IPFS Fetch Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch encrypted file from IPFS")
    try:
        decrypted_pdf = decrypt_pdf_hybrid(
            ciphertext_pdf, 
            diploma.encrypted_key, 
            diploma.iv, 
            private_key_string
        )
    except Exception as e:
        print(f"=== DECRYPTION ERROR DEBUG ===")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"===============================")
        raise HTTPException(
            status_code=401, 
            detail=f"Decryption failed: {str(e)}"
        )
    
    recalculated_hash = calculate_sha256(decrypted_pdf)
    
    if recalculated_hash != diploma.document_hash:
        print(f"Hash Mismatch! Decrypted: {recalculated_hash} vs DB: {diploma.document_hash}")
        raise HTTPException(status_code=400, detail="Integrity check failed. Decrypted file hash mismatch.")
    
    try:
        on_chain_data = contract.functions.getDiploma(diploma.document_hash).call()
        if on_chain_data[6] != 0: 
             raise HTTPException(status_code=400, detail="Diploma is no longer valid on blockchain.")
    except Exception as e:
        print(f"Blockchain verify error: {e}")
        raise HTTPException(status_code=500, detail="Blockchain verification failed")
    
    safe_filename = f"Ijazah_{diploma.diploma_number}.pdf".replace("/", "_")
    
    return StreamingResponse(
        io.BytesIO(decrypted_pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
    )