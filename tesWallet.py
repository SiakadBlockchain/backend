import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from web3 import Web3
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

from eth_account import Account

# Aktifkan fitur audit jika diperlukan (opsional)
Account.enable_unaudited_hdwallet_features()

def generate_avax_wallet():
    # Menghasilkan wallet baru secara acak
    acct = Account.create()
    
    # Address: Alamat publik yang Anda minta (Contoh: 0x123...)
    address = acct.address
    
    # Private Key: Kunci rahasia untuk akses wallet
    private_key = acct.key.hex()
    
    return address, private_key

app = FastAPI()

# --- KONFIGURASI RPC AVALANCHE ---
# Menggunakan RPC URL Subnet yang Anda berikan
AVAX_RPC_URL = "http://127.0.0.1:9654/ext/bc/LtfgTv2tY6f3PUefYWjEaUXcqBr93wT5YYLDPD1EtZzdjP98L/rpc"
w3 = Web3(Web3.HTTPProvider(AVAX_RPC_URL))

# --- SETUP ENKRIPSI ---
MASTER_KEY = os.getenv("MASTER_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(MASTER_KEY.encode())

# Simulasi Database
db_wallets = {}

# Schema Data
class WalletUpdate(BaseModel):
    is_connected: bool

# --- HELPER FUNCTIONS ---

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

# --- ROUTES ---

@app.get("/system/rpc-status")
async def check_rpc():
    if w3.is_connected():
        return {"status": "connected", "endpoint": AVAX_RPC_URL, "block_number": w3.eth.block_number}
    raise HTTPException(status_code=503, detail="Gagal terhubung ke RPC Avalanche")

@app.post("/wallet/generate/{student_id}")
async def create_wallet(student_id: str):
    if student_id in db_wallets:
        raise HTTPException(status_code=400, detail="Wallet sudah terdaftar")
    
    # Gunakan generator ECDSA untuk blockchain
    address, private_key = generate_avax_wallet()
    
    # Tetap enkripsi private key sebelum disimpan
    encrypted_pk = cipher_suite.encrypt(private_key.encode()).decode()
    
    db_wallets[student_id] = {
        "student_id": student_id,
        "blockchain_address": address, # Inilah Address AVAX Anda
        "private_key_encrypted": encrypted_pk,
        "is_connected": False
    }
    
    return {
        "status": "success",
        "student_id": student_id,
        "avax_address": address,
        "info": "Gunakan address ini untuk cek saldo di RPC"
    }

@app.get("/wallet/status/{student_id}")
async def get_wallet_status(student_id: str):
    wallet = db_wallets.get(student_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet tidak ditemukan")
    
    return wallet

@app.patch("/wallet/connection/{student_id}")
async def toggle_connection(student_id: str, update: WalletUpdate):
    if student_id not in db_wallets:
        raise HTTPException(status_code=404, detail="Wallet tidak ditemukan")
    
    if not w3.is_connected():
        raise HTTPException(status_code=503, detail="RPC Node tidak aktif, tidak bisa mengubah status koneksi")

    db_wallets[student_id]["is_connected"] = update.is_connected
    return {"message": "Status diperbarui", "is_connected": update.is_connected}

@app.get("/wallet/balance/{address}")
async def get_onchain_balance(address: str):
    # Route ini mendemonstrasikan komunikasi backend ke blockchain via RPC
    try:
        # Validasi format address
        checksum_address = w3.to_checksum_address(address)
        balance_wei = w3.eth.get_balance(checksum_address)
        balance_avax = w3.from_wei(balance_wei, 'ether')
        
        return {
            "address": checksum_address,
            "balance_avax": float(balance_avax),
            "unit": "AVAX"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal mengambil saldo: {str(e)}")

@app.post("/wallet/sign-data/{student_id}")
async def sign_data(student_id: str, message: str):
    wallet = db_wallets.get(student_id)
    if not wallet or not wallet["is_connected"]:
        raise HTTPException(status_code=403, detail="Wallet belum terhubung")
    
    # Proses dekripsi untuk penggunaan sementara
    encrypted_key = wallet["private_key_encrypted"]
    private_key_pem = cipher_suite.decrypt(encrypted_key.encode()).decode()
    
    # Di sini Anda bisa menambahkan logika signing RSA sesuai kebutuhan
    return {
        "status": "Success", 
        "student_id": student_id,
        "info": "Data signed using RSA Private Key"
    }

@app.delete("/wallet/remove/{student_id}")
async def delete_wallet(student_id: str):
    if student_id in db_wallets:
        del db_wallets[student_id]
        return {"message": "Wallet berhasil dihapus"}
    raise HTTPException(status_code=404, detail="Wallet tidak ditemukan")