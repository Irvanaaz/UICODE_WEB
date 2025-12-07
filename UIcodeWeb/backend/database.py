import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# 1. Load data rahasia dari .env
load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Buat Mesin Database
# connect_args diset kosong karena kita pakai Postgres (beda kalau SQLite)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Buat Session (Sesi transaksi data)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base Class (Induk dari semua tabel nanti)
Base = declarative_base()

# 5. Fungsi Helper: "Pinjam koneksi sebentar, lalu tutup"
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()