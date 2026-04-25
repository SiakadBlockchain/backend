"# backend" 

### Database Route

POST   /users              → create user
GET    /users              → get all users
GET    /users/<id>         → get detail user
PUT    /users/<id>         → update user
DELETE /users/<id>         → delete user

POST   /universities
GET    /universities
GET    /universities/<id>
PUT    /universities/<id>
DELETE /universities/<id>

POST   /students
GET    /students
GET    /students/<id>
PUT    /students/<id>
DELETE /students/<id>

POST   /diplomas                  → issue ijazah
GET    /diplomas
GET    /diplomas/<id>
PUT    /diplomas/<id>
DELETE /diplomas/<id>
POST   /diplomas/<id>/revoke      → revoke ijazah
POST   /diplomas/verify           → verifikasi (pakai document_hash)

POST   /wallets
GET    /wallets
GET    /wallets/<id>
PUT    /wallets/<id>
DELETE /wallets/<id>

GET    /transactions
GET    /transactions/<id>

GET    /verification-logs

POST   /auth/login
POST   /auth/register

### Test Endpoint

# Users

{
  "name" : "Dummy User",
  "email" : "dummy@gmail.com",
  "password" : "dummy",
  "role" : "admin",
  "university_id" : "342a3d25-be75-4b92-997d-1c2a75b8fe63"
}

# Students

{
  "name": "Dummy Students",
  "nim": "12345678",
  "university_id": "342a3d25-be75-4b92-997d-1c2a75b8fe63"
}

# Diplomas

{
  "student_id": "68ff79d4-0280-4fac-8bfb-e21eb3dfb97c",
  "university_id": "342a3d25-be75-4b92-997d-1c2a75b8fe63",
  "diploma_number": "AX0A",
  "ipfs_cid": "CID",
  "document_hash": "haashas",
  "tx_hash": "hasdada",
  "block_number": "1"
}

{
  "student_id": "68ff79d4-0280-4fac-8bfb-e21eb3dfb97c",
  "university_id": "342a3d25-be75-4b92-997d-1c2a75b8fe63",
  "diploma_number": "AX0A",
  "ipfs_cid": "CIDAX",
  "document_hash": "haashas",
  "tx_hash": "hasdada",
  "block_number": "1",
  "status": "valid"
}

# Wallets

{
  "user_id": "5f159c5d-7537-486f-bd98-77f50ec131b8",
  "wallet_address": "wld-add",
  "is_primary": true,
  "verified": true
}

# Auth Register

{
  "name" : "Dummy 2",
  "email" : "dummyRegister@gmail.com",
  "password" : "dummy",
  "role" : "admin",
  "university_id" : "342a3d25-be75-4b92-997d-1c2a75b8fe63"
}

# Auth Login

{
  "email" : "dummyRegister@gmail.com",
  "password" : "dummy"
}
