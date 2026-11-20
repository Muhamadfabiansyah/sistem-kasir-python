
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Deteksi apakah aplikasi berjalan di Vercel
IS_VERCEL = os.environ.get("VERCEL") == "1"


class Config:
    """Konfigurasi dasar aplikasi POS"""

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "development-only-change-this-key"
    )

    # Database:
    # Vercel hanya menggunakan /tmp untuk penulisan sementara.
    if IS_VERCEL:
        INSTANCE_DIR = "/tmp/instance"
    else:
        INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

    os.makedirs(INSTANCE_DIR, exist_ok=True)

    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH",
        os.path.join(INSTANCE_DIR, "pos.db")
    )

    # Folder upload lokal
    # Di Vercel folder aplikasi tidak dapat ditulisi.
    UPLOAD_FOLDER = os.path.join(
        BASE_DIR, "static", "uploads"
    )

    if not IS_VERCEL:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    ALLOWED_EXTENSIONS = {
        "png", "jpg", "jpeg", "webp", "gif"
    }

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
