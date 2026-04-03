from sqlalchemy import create_engine, Column, String, Text, Boolean, Enum, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import uuid

from database import engine

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    name = Column(String(255))
    email = Column(String(255), unique=True)
    password_hash = Column(Text)
    role = Column(Enum('admin', 'staff', 'validator'))
    university_id = Column(CHAR(36), ForeignKey("universities.id"))
    created_at = Column(TIMESTAMP)

    university = relationship("University", back_populates="users")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    user_id = Column(CHAR(36), ForeignKey("users.id"))
    wallet_address = Column(String(255), unique=True)
    is_primary = Column(Boolean)
    verified = Column(Boolean)
    created_at = Column(TIMESTAMP)

    user = relationship("User")


class University(Base):
    __tablename__ = "universities"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    name = Column(String(255))
    accreditation = Column(Enum('A', 'B', 'C'))
    wallet_address = Column(String(255))
    is_active = Column(Boolean)
    created_at = Column(TIMESTAMP)

    users = relationship("User", back_populates="university")


class Student(Base):
    __tablename__ = "students"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    name = Column(String(255))
    nim = Column(String(100), unique=True)
    university_id = Column(CHAR(36), ForeignKey("universities.id"))
    created_at = Column(TIMESTAMP)

    university = relationship("University")


class Diploma(Base):
    __tablename__ = "diplomas"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)

    student_id = Column(CHAR(36), ForeignKey("students.id"))
    university_id = Column(CHAR(36), ForeignKey("universities.id"))

    diploma_number = Column(String(255))

    ipfs_cid = Column(Text)
    document_hash = Column(String(255))

    tx_hash = Column(String(255))
    block_number = Column(BigInteger)

    status = Column(Enum('valid', 'revoked'))

    issued_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)

    student = relationship("Student")
    university = relationship("University")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)

    tx_hash = Column(String(255), unique=True)

    tx_type = Column(Enum(
        'REGISTER_UNIVERSITY',
        'ISSUE_DIPLOMA',
        'VERIFY_DIPLOMA',
        'REVOKE_DIPLOMA',
        'UPDATE_ACCREDITATION'
    ))

    wallet_address = Column(String(255))

    status = Column(Enum('pending', 'success', 'failed'))

    block_number = Column(BigInteger)
    gas_used = Column(BigInteger)

    created_at = Column(TIMESTAMP)


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    document_hash = Column(String(255))
    result = Column(Enum('valid', 'invalid'))
    checked_at = Column(TIMESTAMP)
    ip_address = Column(String(100))

def init_db():
    Base.metadata.create_all(engine)
    print("All Tables Successfully Created")

if __name__ == "__main__":
    init_db()