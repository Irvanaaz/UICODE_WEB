from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

# --- ENUM COPY ---
# Kita perlu ini agar respon API menampilkan teks yang benar
class RoleEnum(str, Enum):
    MEMBER = "member"
    ADMIN = "admin"

class StatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# --- USER SCHEMAS ---
# Apa yang kita tampilkan ke publik saat ada yang minta data user
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: RoleEnum
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True # Dulu namanya orm_mode

# --- COMPONENT SCHEMAS ---
# Data yang dikirim User saat CREATE
class ComponentCreate(BaseModel):
    # title: str
    category: str
    html_code: str
    css_code: str

# Data yang kita kirim balik ke Frontend (RESPONSE)
class ComponentResponse(BaseModel):
    id: int
    category: str
    html_code: str
    css_code: str
    status: str
    views_count: int
    created_at: datetime
    owner: UserResponse
    
    # TAMBAHAN FIELD LIKE
    likes_count: int = 0
    liked_by_me: bool = False # Nanti diisi True kalau user sudah like

    class Config:
        from_attributes = True