from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import urllib.parse

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "db_siakad_blockchain")

safe_password = urllib.parse.quote_plus(DB_PASSWORD)

engine = create_engine(f"mysql+pymysql://{DB_USER}:{safe_password}@{DB_HOST}/{DB_NAME}")
SessionLocal = sessionmaker(bind=engine)