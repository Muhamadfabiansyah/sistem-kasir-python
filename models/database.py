import os
import sqlite3
from werkzeug.security import generate_password_hash
from config import Config

class Database:
    """
    Class Database mengelola koneksi, pembuatan tabel, integritas transaksi,
    dan inisialisasi data awal (seeding) secara terenkapsulasi.
    """

    def __init__(self, db_path: str = None):
        # Encapsulation: Menyimpan path database di atribut private __db_path
        self.__db_path = db_path if db_path else Config.DATABASE_PATH
        
        # Pastikan direktori database ada
        folder = os.path.dirname(self.__db_path)
        if folder:
            os.makedirs(folder, exist_ok=True)

    @property
    def db_path(self) -> str:
        """Getter untuk membaca path database"""
        return self.__db_path

    def get_connection(self) -> sqlite3.Connection:
        """Membuat dan mengembalikan objek koneksi SQLite dengan konfigurasi Row Factory"""
        conn = sqlite3.connect(self.__db_path)
        conn.row_factory = sqlite3.Row
        # Mengaktifkan dukungan foreign key di SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Membuat seluruh tabel sistem kasir jika belum ada."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. Tabel users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'cashier')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Tabel categories
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Tabel products
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category_id INTEGER,
                cost_price REAL NOT NULL DEFAULT 0,
                price REAL NOT NULL CHECK(price >= 0),
                stock INTEGER NOT NULL CHECK(stock >= 0) DEFAULT 0,
                image TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            );
        """)

        # 4. Tabel transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                cashier_name TEXT NOT NULL,
                subtotal REAL NOT NULL,
                discount REAL NOT NULL DEFAULT 0,
                total REAL NOT NULL,
                cash_paid REAL NOT NULL,
                change_amount REAL NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
        """)

        # 5. Tabel transaction_details
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaction_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                product_id INTEGER,
                product_code TEXT,
                product_name TEXT NOT NULL,
                cost_price REAL NOT NULL DEFAULT 0,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                subtotal REAL NOT NULL,
                FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
            );
        """)

        # 6. Tabel settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_name TEXT NOT NULL,
                store_address TEXT,
                store_phone TEXT,
                receipt_footer TEXT,
                tax_percentage REAL DEFAULT 0,
                currency_symbol TEXT DEFAULT 'Rp'
            );
        """)

        conn.commit()
        conn.close()

        # Jalankan initial seed data
        self.seed_initial_data()

    def seed_initial_data(self):
        """Mengisi data awal secara aman jika database masih kosong."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Inisialisasi Pengaturan Toko
        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO settings (store_name, store_address, store_phone, receipt_footer, tax_percentage, currency_symbol)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "TOKO BERKAH SEJAHTERA",
                "Jl. Sudirman No. 123, Jakarta Pusat",
                "0812-3456-7890",
                "Terima kasih atas kunjungan Anda! Barang yang sudah dibeli tidak dapat ditukar.",
                0.0,
                "Rp"
            ))

        # Inisialisasi Akun Admin dan Kasir
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            admin_user = os.environ.get('ADMIN_INITIAL_USERNAME', 'admin')
            admin_pass = os.environ.get('ADMIN_INITIAL_PASSWORD', 'admin123')
            admin_hash = generate_password_hash(admin_pass)

            cashier_hash = generate_password_hash("kasir123")

            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            """, (admin_user, admin_hash, "Administrator POS", "admin"))

            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            """, ("kasir1", cashier_hash, "Siti Kasir", "cashier"))

        # Inisialisasi Kategori Awal
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            categories_data = [
                ("Makanan Ringan", "Aneka snack, biskuit, dan keripik"),
                ("Minuman", "Minuman dingin, kopi, teh, dan air mineral"),
                ("Sembako", "Beras, minyak goreng, gula, dan kebutuhan pokok"),
                ("Alat Tulis", "Buku, pulpen, dan perlengkapan sekolah/kantor")
            ]
            cursor.executemany("""
                INSERT INTO categories (name, description) VALUES (?, ?)
            """, categories_data)

        # Inisialisasi Produk Awal
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            products_data = [
                ("PRD-001", "Indomie Goreng Original", 1, 2800, 3500, 50, "indomie.png", "Mie instan goreng favorit Indonesia"),
                ("PRD-002", "Air Mineral Aqua 600ml", 2, 2800, 4000, 40, "aqua.png", "Air mineral pegunungan segar"),
                ("PRD-003", "Kopi Kapal Api Special Mix", 2, 1800, 2500, 35, "kopi.png", "Kopi bubuk instan mantap"),
                ("PRD-004", "Chitato Sapi Panggang 68g", 1, 9500, 12000, 25, "chitato.png", "Keripik kentang bergelombang"),
                ("PRD-005", "Minyak Goreng Bimoli 1L", 3, 16000, 19500, 20, "bimoli.png", "Minyak goreng kelapa sawit murni"),
                ("PRD-006", "Gula Pasir Gulaku 1kg", 3, 14000, 17000, 18, "gulaku.png", "Gula tebu pilihan higienis"),
                ("PRD-007", "Teh Botol Sosro 450ml", 2, 4500, 6000, 30, "tehbotol.png", "Teh melati dalam botol"),
                ("PRD-008", "Buku Tulis Sinar Dunia 38", 4, 3000, 4500, 40, "buku.png", "Buku tulis bergaris 38 lembar"),
                ("PRD-009", "Pulpen Pilot G2 0.5mm", 4, 12000, 16000, 15, "pulpen.png", "Pulpen gel hitam berkualitas")
            ]
            cursor.executemany("""
                INSERT INTO products (code, name, category_id, cost_price, price, stock, image, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, products_data)

        conn.commit()
        conn.close()

# Singleton DB instance
db_instance = Database()
