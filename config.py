import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Konfigurasi dasar aplikasi POS"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pos-super-secret-key-prod-2026-v2')
    
    # Path Database SQLite (Disimpan di folder instance agar persisten)
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(INSTANCE_DIR, 'pos.db'))
    
    # Upload Gambar
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Maksimal 5 MB
    
    # Pengaturan Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 1 hari (detik)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
