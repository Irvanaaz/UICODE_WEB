-- =============================================
-- 1. BERSIH-BERSIH (RESET)
-- =============================================
-- Hapus tabel lama jika ada, biar tidak error saat dijalankan ulang
DROP TABLE IF EXISTS component_likes CASCADE;
DROP TABLE IF EXISTS ui_components CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TYPE IF EXISTS user_role CASCADE;
DROP TYPE IF EXISTS code_status CASCADE;

-- =============================================
-- 2. MEMBUAT TIPE DATA KHUSUS (ENUM)
-- =============================================

-- Tipe untuk membedakan Admin dan Member biasa
CREATE TYPE user_role AS ENUM ('member', 'admin');

-- Tipe untuk status moderasi kode (Jantungnya fitur Approval)
CREATE TYPE code_status AS ENUM ('pending', 'approved', 'rejected');

-- =============================================
-- 3. TABEL USER (PENGGUNA)
-- =============================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Password harus terenkripsi
    
    -- Profil
    avatar_url VARCHAR(255),
    bio TEXT,
    
    -- Role & Status
    role user_role DEFAULT 'member', -- Default user biasa
    is_online BOOLEAN DEFAULT FALSE, -- Untuk fitur admin "Lihat User Online"
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index biar login & pencarian user cepat
CREATE INDEX idx_users_email ON users(email);

-- =============================================
-- 4. TABEL UI COMPONENTS (KARYA USER)
-- =============================================
CREATE TABLE ui_components (
    id SERIAL PRIMARY KEY,
    
    -- Relasi: Kode ini milik siapa?
    -- ON DELETE CASCADE: Kalau User dihapus, semua kodenya ikut terhapus
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Data Kode
    title VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL, 
    html_code TEXT NOT NULL,
    css_code TEXT NOT NULL,
    
    -- Status Moderasi (Fitur Admin: Accept/Reject)
    status code_status DEFAULT 'pending', 
    
    -- Statistik
    views_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index untuk mempercepat Filter di Halaman Home & Admin Dashboard
CREATE INDEX idx_components_status ON ui_components(status);
CREATE INDEX idx_components_category ON ui_components(category);
CREATE INDEX idx_components_user_id ON ui_components(user_id);

-- =============================================
-- 5. TABEL LIKES (FITUR FAVORIT)
-- =============================================
CREATE TABLE component_likes (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    component_id INTEGER REFERENCES ui_components(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- KUNCI UTAMA GABUNGAN:
    -- Mencegah 1 User men-like 1 Komponen lebih dari sekali
    PRIMARY KEY (user_id, component_id) 
);

-- =============================================
-- 6. DATA AWAL (SEEDING) - WAJIB DIJALANKAN
-- =============================================

-- A. Masukkan AKUN ADMIN KHUSUS (Sesuai Request)
-- Catatan: Di aplikasi asli, password ini harus di-hash. 
-- Tapi karena ini query manual, kita masukkan stringnya dulu.
INSERT INTO users (username, email, password_hash, role, avatar_url, is_online, bio) 
VALUES 
(
    'IrvanSuperAdmin', 
    'irvanziz898@gmail.com', 
    'Irvan121508?', -- Nanti backend yg tugasnya mengenkripsi ini
    'admin', -- PERHATIKAN: Role-nya ADMIN
    'https://ui-avatars.com/api/?name=Irvan+Admin&background=0D8ABC&color=fff',
    TRUE,
    'Owner & Creator of UICODE'
);

-- B. Masukkan User Biasa (Untuk Tes)
INSERT INTO users (username, email, password_hash, role, avatar_url, is_online, bio) 
VALUES 
(
    'user1', 
    'user1@uicode.com', 
    '123456', 
    'member', -- Role MEMBER
    'https://ui-avatars.com/api/?name=Frontend+Master',
    FALSE,
    'Belajar CSS itu seru!'
);

INSERT INTO users (username, email, password_hash, role, avatar_url, is_online, bio) 
VALUES 
(
    'user2', 
    'user2@uicode.com', 
    '123456', 
    'member', -- Role MEMBER
    'https://ui-avatars.com/api/?name=Frontend+Master',
    True,
    'Aku suka belajar koding!'
);

-- C. Masukkan Contoh Komponen (Untuk Tes Alur Moderasi)

-- 1. Status APPROVED (Akan muncul di Home) - Milik FrontendMaster
INSERT INTO ui_components (user_id, title, category, html_code, css_code, status) 
VALUES (2, 'Tombol Biru Glossy', 'button', '<button>Klik Saya</button>', '.btn { background: blue; }', 'approved');

-- 2. Status PENDING (Akan muncul di Dashboard Admin Irvan) - Milik FrontendMaster
INSERT INTO ui_components (user_id, title, category, html_code, css_code, status) 
VALUES (2, 'Card Glassmorphism', 'card', '<div class="card">Halo</div>', '.card { backdrop-filter: blur(10px); }', 'pending');

-- 3. Status REJECTED (Akan muncul di Profil FrontendMaster tab Rejected)
INSERT INTO ui_components (user_id, title, category, html_code, css_code, status) 
VALUES (2, 'Input Rusak', 'input', '<input>', 'input { display: none; }', 'rejected');

-- D. Masukkan Contoh Like
-- Admin Irvan menyukai tombol buatan FrontendMaster
INSERT INTO component_likes (user_id, component_id) VALUES (1, 1);