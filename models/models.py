from sqlalchemy import create_engine, Column, String, Text, Boolean, Enum, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import declarative_base, relationship
import uuid

from databases.connection import engine

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    name = Column(String(255))
    email = Column(String(255), unique=True)
    password_hash = Column(Text)
    role = Column(Enum('admin', 'university', 'validator'))
    university_id = Column(CHAR(36), ForeignKey("universities.id"), nullable=True)
    public_key = Column(Text)
    created_at = Column(TIMESTAMP)

    university = relationship("University", back_populates="users")


class University(Base):
    __tablename__ = "universities"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    name = Column(String(255))
    accreditation = Column(Enum('A', 'B', 'C'))
    created_at = Column(TIMESTAMP)

    users = relationship("User", back_populates="university")
    studies = relationship("Study", back_populates="university")

class Student(Base):
    __tablename__ = "students"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    name = Column(String(255))
    public_key = Column(Text)
    rsa_private_key_encrypted = Column(Text)
    ktp_number = Column(String(20), unique=True)
    phone_number = Column(String(20), unique=True)
    is_phone_verified = Column(Boolean, default=False)
    place_and_date_of_birth = Column(String(255))
    email = Column(String(255), unique=True)
    password_hash = Column(Text)
    otp_secret = Column(String(10), nullable=True)
    wallet = relationship("Wallet", back_populates="student", uselist=False)
    
    created_at = Column(TIMESTAMP)

    studies = relationship("Study", back_populates="student")
    diplomas = relationship("Diploma", back_populates="student")

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    student_id = Column(CHAR(36), ForeignKey("students.id"), unique=True)
    blockchain_address = Column(String(255), unique=True)
    private_key_encrypted = Column(Text) 
    is_connected = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP)

    student = relationship("Student", back_populates="wallet")


class Study(Base):
    __tablename__ = "studies"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    student_id = Column(CHAR(36), ForeignKey("students.id"))
    university_id = Column(CHAR(36), ForeignKey("universities.id"))
    major = Column(String(255))
    level = Column(String(50))
    nim = Column(String(100), unique=True)

    student = relationship("Student", back_populates="studies")
    university = relationship("University", back_populates="studies")
    diplomas = relationship("Diploma", back_populates="study")


class Diploma(Base):
    __tablename__ = "diplomas"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    studies_id = Column(CHAR(36), ForeignKey("studies.id"))
    graduationYear = Column(String(4))
    university_id = Column(CHAR(36), ForeignKey("universities.id"))
    student_id = Column(CHAR(36), ForeignKey("students.id"))

    diploma_number = Column(String(255))
    ipfs_cid = Column(Text)
    document_hash = Column(String(255))
    encrypted_key = Column(Text, nullable=True)
    iv = Column(String(255), nullable=True)
    tx_hash = Column(String(255))
    block_number = Column(BigInteger)
    status = Column(Enum('valid', 'revoked', 'pending'))
    issued_at = Column(TIMESTAMP)

    study = relationship("Study", back_populates="diplomas")
    student = relationship("Student", back_populates="diplomas")
    university = relationship("University")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(CHAR(36), primary_key=True, default=generate_uuid)
    reference_id = Column(CHAR(36), nullable=True)
    tx_hash = Column(String(255), unique=True)
    tx_type = Column(Enum(
        'REGISTER_UNIVERSITY',
        'ISSUE_DIPLOMA',
        'VERIFY_DIPLOMA',
        'REVOKE_DIPLOMA',
        'UPDATE_ACCREDITATION'
    ))
    status = Column(Enum('pending', 'success', 'failed'))
    block_number = Column(BigInteger)
    gas_used = Column(BigInteger)
    created_at = Column(TIMESTAMP)

def init_db(engine):
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_db(engine)