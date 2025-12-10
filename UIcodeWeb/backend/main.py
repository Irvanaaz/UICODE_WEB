from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import JWTError, jwt
from fastapi.middleware.cors import CORSMiddleware

# Import file buatan kita
import models, schemas, auth
from database import engine, get_db

# Setup Tabel (Jaga-jaga)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="UICODE API - Final Version")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- KEAMANAN & AUTH ---
# PENTING: auto_error=False agar tamu tidak kena error 401 di halaman Feed
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# Fungsi: Mengecek Siapa yang Login (Wajib Login)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau kadaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Fungsi Baru: Cek User tapi TIDAK Wajib Login (Untuk Feed)
def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        if not token: return None
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None: return None
        user = db.query(models.User).filter(models.User.email == email).first()
        return user
    except:
        return None # Kalau token error, anggap saja tamu

# Fungsi: Mengecek apakah User adalah ADMIN
def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin": 
        raise HTTPException(status_code=403, detail="Maaf, Anda bukan Admin!")
    return current_user

# --- ENDPOINT AUTH ---
@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Cek Email Kembar
    db_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar!")

    # 2. Cek Username Kembar
    db_username = db.query(models.User).filter(models.User.username == user.username).first()
    if db_username:
        raise HTTPException(status_code=400, detail="Username sudah dipakai!")

    # 3. Hash Password (Enkripsi)
    hashed_password = auth.get_password_hash(user.password)

    # 4. Simpan User Baru
    new_user = models.User(
        email=user.email,
        username=user.username,
        password_hash=hashed_password,
        role="member",
        avatar_url=None,
        is_online=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau Password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/", response_model=List[schemas.UserResponse])
def read_users(current_user: models.User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return db.query(models.User).all()

# --- ENDPOINT COMPONENTS ---
@app.post("/components/", response_model=schemas.ComponentResponse)
def create_component(
    component: schemas.ComponentCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_comp = models.UIComponent(
        category=component.category,
        html_code=component.html_code,
        css_code=component.css_code,
        user_id=current_user.id,
        status="pending"
    )
    db.add(new_comp)
    db.commit()
    db.refresh(new_comp)
    return new_comp

@app.get("/components/{component_id}", response_model=schemas.ComponentResponse)
def get_component_detail(
    component_id: int, 
    db: Session = Depends(get_db)
):
    # Kita tidak filter status, agar Admin bisa lihat yang 'pending' juga
    comp = db.query(models.UIComponent).filter(models.UIComponent.id == component_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Komponen tidak ditemukan")
    comp.likes_count = len(comp.likes)
    comp.liked_by_me = False
    
    return comp

# --- ENDPOINT TOGGLE LIKE (BARU) ---
@app.post("/components/{component_id}/like")
def toggle_like(
    component_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Wajib Login
):
    # 1. Cek Komponen Ada?
    comp = db.query(models.UIComponent).filter(models.UIComponent.id == component_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Komponen tidak ditemukan")

    # 2. Cek Like Existing
    existing_like = db.query(models.ComponentLike).filter(
        models.ComponentLike.user_id == current_user.id,
        models.ComponentLike.component_id == component_id
    ).first()

    if existing_like:
        db.delete(existing_like)
        db.commit()
        return {"status": "unliked", "likes_count": len(comp.likes)}
    else:
        new_like = models.ComponentLike(user_id=current_user.id, component_id=component_id)
        db.add(new_like)
        db.commit()
        return {"status": "liked", "likes_count": len(comp.likes)}

# --- ENDPOINT PUBLIC FEED (UPDATE LOGIKA LIKE) ---
@app.get("/feed", response_model=List[schemas.ComponentResponse])
def get_public_feed(
    category: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional) # Optional Auth
):
    query = db.query(models.UIComponent).join(models.User).filter(models.UIComponent.status == "approved")
    
    if category and category != "All":
        query = query.filter(models.UIComponent.category == category)
    
    if q:
        query = query.filter(models.User.username.ilike(f"%{q}%"))
    
    results = query.order_by(models.UIComponent.created_at.desc()).all()

    # Hitung Like & Cek Status Liked
    for item in results:
        item.likes_count = len(item.likes)
        item.liked_by_me = False
        if current_user:
            for like in item.likes:
                if like.user_id == current_user.id:
                    item.liked_by_me = True
                    break
    
    return results

# --- ENDPOINT ADMIN ---
@app.get("/admin/pending", response_model=List[schemas.ComponentResponse])
def get_pending_items(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin)):
    return db.query(models.UIComponent).filter(models.UIComponent.status == "pending").all()

@app.put("/admin/review/{component_id}")
def review_component(
    component_id: int, 
    action: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    comp = db.query(models.UIComponent).filter(models.UIComponent.id == component_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Komponen tidak ditemukan")
    
    if action.lower() == "approve":
        comp.status = "approved"
    elif action.lower() == "reject":
        comp.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Action salah")
    
    db.commit()
    return {"message": "Sukses update status"}

@app.delete("/components/{component_id}")
def delete_component(
    component_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    comp = db.query(models.UIComponent).filter(models.UIComponent.id == component_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Komponen tidak ditemukan")
    
    db.delete(comp)
    db.commit()
    return {"message": "Komponen berhasil dihapus permanen"}

# --- ENDPOINT USER PROFILE ---
class AvatarUpdate(schemas.BaseModel):
    avatar_url: str

@app.put("/users/me/avatar")
def update_avatar(
    data: AvatarUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    current_user.avatar_url = data.avatar_url
    db.commit()
    return {"message": "Avatar updated", "new_url": current_user.avatar_url}

@app.get("/users/me/components", response_model=List[schemas.ComponentResponse])
def get_my_components(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Ambil semua komponen user
    comps = db.query(models.UIComponent).filter(models.UIComponent.user_id == current_user.id).all()
    
    # Hitung Likes Count manual (Sama seperti di Feed)
    for item in comps:
        item.likes_count = len(item.likes)
        # Kita set true karena ini punya sendiri (opsional, buat UI biar tau ini punya dia)
        item.liked_by_me = False 
        
    return comps

@app.get("/stats/categories")
def get_category_counts(db: Session = Depends(get_db)):
    # 1. Hitung total semua komponen Approved
    total_approved = db.query(models.UIComponent).filter(models.UIComponent.status == "approved").count()
    
    # 2. Hitung per kategori
    # Query SQL: SELECT category, COUNT(id) FROM ui_components WHERE status='approved' GROUP BY category
    stats = db.query(
        models.UIComponent.category, 
        func.count(models.UIComponent.id)
    ).filter(
        models.UIComponent.status == "approved"
    ).group_by(
        models.UIComponent.category
    ).all()
    
    # Ubah hasil query jadi Dictionary biar gampang dibaca JSON
    # Contoh hasil: {"button": 5, "card": 2, "input": 10}
    result = {category: count for category, count in stats}
    
    # Tambahkan total "All"
    result["All"] = total_approved
    
    return result
