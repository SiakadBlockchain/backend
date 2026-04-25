from databases.connection import SessionLocal
from models.models import User, Wallet, University, Student, Diploma, Transaction, VerificationLog

from datetime import datetime
import uuid
import random

def generate_uuid():
    return str(uuid.uuid4())

def seed_data():
    session = SessionLocal()

    try:
        print("Seeding data dummy...")

        uni = University(
            id=generate_uuid(),
            name="Universitas Dummy",
            accreditation=random.choice(['A', 'B', 'C']),
            wallet_address="0xUNI",
            is_active=True,
            created_at=datetime.now()
        )
        session.add(uni)
        session.flush()

        user = User(
            id=generate_uuid(),
            name="Admin Dummy",
            email=f"admin{random.randint(1,999)}@mail.com",
            password_hash="hashed",
            role="admin",
            university_id=uni.id,
            created_at=datetime.now()
        )
        session.add(user)
        session.flush()

        wallet = Wallet(
            id=generate_uuid(),
            user_id=user.id,
            wallet_address=f"0x{random.randint(1000,9999)}",
            is_primary=True,
            verified=True,
            created_at=datetime.now()
        )
        session.add(wallet)

        student = Student(
            id=generate_uuid(),
            name="Mahasiswa Dummy",
            nim=str(random.randint(100000,999999)),
            university_id=uni.id,
            created_at=datetime.now()
        )
        session.add(student)
        session.flush()

        diploma = Diploma(
            id=generate_uuid(),
            student_id=student.id,
            university_id=uni.id,
            diploma_number=f"DIP-{random.randint(100,999)}",
            ipfs_cid="QmDummy",
            document_hash=f"HASH{random.randint(1000,9999)}",
            tx_hash=f"0xTX{random.randint(1000,9999)}",
            block_number=random.randint(1000,5000),
            status="valid",
            issued_at=datetime.now(),
            created_at=datetime.now()
        )
        session.add(diploma)

        tx = Transaction(
            id=generate_uuid(),
            tx_hash=diploma.tx_hash,
            tx_type="ISSUE_DIPLOMA",
            wallet_address=wallet.wallet_address,
            status="success",
            block_number=diploma.block_number,
            gas_used=21000,
            created_at=datetime.now()
        )
        session.add(tx)

        session.commit()
        print("Seeding data dummy successfully!")

    except Exception as e:
        session.rollback()
        print("Error:", e)

    finally:
        session.close()

def clear_data():
    session = SessionLocal()

    try:
        print("Clearing data...")

        session.query(VerificationLog).delete()
        session.query(Transaction).delete()
        session.query(Diploma).delete()
        session.query(Student).delete()
        session.query(Wallet).delete()
        session.query(User).delete()
        session.query(University).delete()

        session.commit()
        print("Data cleared successfully!")

    except Exception as e:
        session.rollback()
        print("Error:", e)

    finally:
        session.close()

if __name__ == "__main__":
    # seed_data()
    clear_data()