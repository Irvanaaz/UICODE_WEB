import os
from datetime import datetime, timedelta
from typing import Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Konfigurasi Keamanan (Ambil dari .env atau default)
SECRET_KEY = os.getenv("SECRET_KEY", "rahasia_super_uicode_123") # Ganti ini nanti di production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Setup Hashing Password (Bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- FUNGSI 1: VERIFIKASI PASSWORD ---
# Membandingkan password ketikan user vs hash di database
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- FUNGSI 2: BIKIN HASH PASSWORD ---
# Mengubah password biasa jadi kode acak (untuk Register nanti)
def get_password_hash(password):
    return pwd_context.hash(password)

# --- FUNGSI 3: BIKIN TOKEN JWT ---
# Membuat "Tiket Masuk" digital
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt