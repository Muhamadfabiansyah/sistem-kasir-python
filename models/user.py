import sqlite3
from typing import Optional, List, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db_instance

class User:
    """
    Class User mengelola akun pengguna, autentikasi, enkripsi password, dan otorisasi role.
    Menerapkan Encapsulation pada atribut private __password_hash.
    """

    def __init__(self, id: Optional[int], username: str, password_hash: str,
                 full_name: str, role: str, created_at: Optional[str] = None):
        self.id = id
        self.username = username.strip().lower()
        self.full_name = full_name.strip()
        self.created_at = created_at

        # Encapsulation: Password hash disimpan private
        self.__password_hash = password_hash
        self.__role = "cashier"
        self.role = role

    # ----------------------------- PROPERTY & SETTER --------------------------
    @property
    def role(self) -> str:
        """Getter role pengguna (admin / cashier)"""
        return self.__role

    @role.setter
    def role(self, value: str):
        val = value.strip().lower()
        if val not in ('admin', 'cashier'):
            raise ValueError("Role pengguna harus bernilai 'admin' atau 'cashier'.")
        self.__role = val

    # --------------------------------- METHOD ---------------------------------
    def check_password(self, password: str) -> bool:
        """Memverifikasi password menggunakan hashing aman Werkzeug."""
        if not self.__password_hash or not password:
            return False
        return check_password_hash(self.__password_hash, password)

    def set_password(self, new_password: str):
        """Mengatur password baru dengan hashing otomatis."""
        if not new_password or len(new_password) < 4:
            raise ValueError("Password minimal terdiri dari 4 karakter.")
        self.__password_hash = generate_password_hash(new_password)

    def is_admin(self) -> bool:
        """Cek apakah user adalah administrator"""
        return self.__role == "admin"

    def to_dict(self) -> Dict[str, Any]:
        """Konversi user ke dictionary (tanpa mengekspos hash password)."""
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.__role,
            "is_admin": self.is_admin(),
            "created_at": self.created_at
        }

    # ------------------------------ CLASS METHOD ------------------------------
    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> Optional['User']:
        if row is None:
            return None
        return cls(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            full_name=row["full_name"],
            role=row["role"],
            created_at=row["created_at"]
        )

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional['User']:
        """Melakukan autentikasi login pengguna."""
        user = cls.get_by_username(username)
        if user and user.check_password(password):
            return user
        return None

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """Mendapatkan data pengguna berdasarkan ID."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return cls.from_db_row(row)

    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """Mendapatkan data pengguna berdasarkan Username."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip().lower(),))
        row = cursor.fetchone()
        conn.close()
        return cls.from_db_row(row)

    @classmethod
    def get_all(cls) -> List['User']:
        """Mengambil seluruh data akun pengguna."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY role ASC, full_name ASC")
        rows = cursor.fetchall()
        conn.close()
        return [cls.from_db_row(r) for r in rows]

    @classmethod
    def create(cls, username: str, password: str, full_name: str, role: str) -> 'User':
        """Membuat akun pengguna baru."""
        clean_user = username.strip().lower()
        if cls.get_by_username(clean_user):
            raise ValueError(f"Username '{clean_user}' sudah digunakan.")
        if len(password) < 4:
            raise ValueError("Password minimal 4 karakter.")

        p_hash = generate_password_hash(password)
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
        """, (clean_user, p_hash, full_name.strip(), role.strip().lower()))
        uid = cursor.lastrowid
        conn.commit()
        conn.close()
        return cls.get_by_id(uid)

    @classmethod
    def update(cls, user_id: int, full_name: str, role: str, new_password: Optional[str] = None) -> bool:
        """Memperbarui informasi profil atau password pengguna."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        if new_password and new_password.strip():
            p_hash = generate_password_hash(new_password.strip())
            cursor.execute("""
                UPDATE users SET full_name = ?, role = ?, password_hash = ? WHERE id = ?
            """, (full_name.strip(), role.strip().lower(), p_hash, user_id))
        else:
            cursor.execute("""
                UPDATE users SET full_name = ?, role = ? WHERE id = ?
            """, (full_name.strip(), role.strip().lower(), user_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    @classmethod
    def delete(cls, user_id: int) -> bool:
        """Menghapus akun pengguna."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
