from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base
import datetime

# --- B. TABEL USERS ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    avatar_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    role = Column(String, default="member") 
    is_online = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relasi
    components = relationship("UIComponent", back_populates="owner", cascade="all, delete")
    likes = relationship("ComponentLike", back_populates="user", cascade="all, delete")

# --- C. TABEL UI COMPONENTS (Karya) ---
class UIComponent(Base):
    __tablename__ = "ui_components"

    id = Column(Integer, primary_key=True, index=True)
    # title = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    html_code = Column(Text, nullable=False)
    css_code = Column(Text, nullable=False)
    
    # --- SOLUSI ANTI-GAGAL DI SINI JUGA ---
    status = Column(String, default="pending", index=True)
    
    views_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # Relasi
    owner = relationship("User", back_populates="components")
    likes = relationship("ComponentLike", back_populates="component", cascade="all, delete")

# --- D. TABEL LIKES ---
class ComponentLike(Base):
    __tablename__ = "component_likes"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    component_id = Column(Integer, ForeignKey("ui_components.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="likes")
    component = relationship("UIComponent", back_populates="likes")