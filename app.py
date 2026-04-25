from fastapi import FastAPI
from routes import users, universities, students, diplomas, wallets, transactions, auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SIAKAD Blockchain API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/siakadBlockchain/api"

app.include_router(
    users.router,
    prefix=f"{API_PREFIX}/users",
    tags=["Users"]
)

app.include_router(
    universities.router,
    prefix=f"{API_PREFIX}/universities",
    tags=["Universities"]
)

app.include_router(
    students.router,
    prefix=f"{API_PREFIX}/students",
    tags=["Students"]
)

app.include_router(
    diplomas.router,
    prefix=f"{API_PREFIX}/diplomas",
    tags=["Diplomas"]
)

app.include_router(
    wallets.router,
    prefix=f"{API_PREFIX}/wallets",
    tags=["Wallets"]
)

app.include_router(
    transactions.router,
    prefix=f"{API_PREFIX}/transactions",
    tags=["Transactions"]
)

app.include_router(
    auth.router,
    prefix=f"{API_PREFIX}/auth",
    tags=["Authentication"]
)

@app.get(f"{API_PREFIX}/")
def root():
    return {"message": "API Gateway is running"}