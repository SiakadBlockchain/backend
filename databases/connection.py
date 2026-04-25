from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_USER = "root"
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_NAME = "db_siakad_blockchain"

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
SessionLocal = sessionmaker(bind=engine)