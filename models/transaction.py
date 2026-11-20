import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from models.database import db_instance

class Transaction:
    """
    Class Transaction merepresentasikan data transaksi penjualan / checkout.
    Menerapkan:
    - Encapsulation: Atribut private __total, __cash_paid, __change_amount
    - Static Method: Kalkulasi diskon, validasi pembayaran, dan pembuatan invoice unik
    - Class Method: Pengambilan riwayat dan statistik laporan dari database
    """

    def __init__(self, id: Optional[int], invoice_number: str, user_id: Optional[int],
                 cashier_name: str, subtotal: float, discount: float, total: float,
                 cash_paid: float, change_amount: float, payment_method: str = "cash",
                 notes: Optional[str] = None, created_at: Optional[str] = None,
                 items: Optional[List[Dict[str, Any]]] = None):
        self.id = id
        self.invoice_number = invoice_number
        self.user_id = user_id
        self.cashier_name = cashier_name
        self.subtotal = float(subtotal)
        self.discount = float(discount)
        self.payment_method = payment_method or "cash"
        self.notes = notes or ""
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.items = items or []

        # Atribut Private (Encapsulation)
        self.__total = 0.0
        self.__cash_paid = 0.0
        self.__change_amount = 0.0

        # Inisialisasi melalui setter
        self.total = total
        self.cash_paid = cash_paid
        self.change_amount = change_amount

    # ----------------------------- PROPERTY & SETTER --------------------------
    @property
    def total(self) -> float:
        """Getter total tagihan akhir"""
        return self.__total

    @total.setter
    def total(self, value: float):
        val = float(value)
        if val < 0:
            raise ValueError("Total pembayaran tidak boleh bernilai negatif.")
        self.__total = val

    @property
    def cash_paid(self) -> float:
        """Getter nominal uang yang dibayarkan pelanggan"""
        return self.__cash_paid

    @cash_paid.setter
    def cash_paid(self, value: float):
        val = float(value)
        if val < 0:
            raise ValueError("Uang pembayaran tidak boleh negatif.")
        self.__cash_paid = val

    @property
    def change_amount(self) -> float:
        """Getter uang kembalian pelanggan"""
        return self.__change_amount

    @change_amount.setter
    def change_amount(self, value: float):
        val = float(value)
        if val < 0:
            raise ValueError("Uang kembalian tidak boleh negatif.")
        self.__change_amount = val

    # ----------------------------- STATIC METHOD ------------------------------
    @staticmethod
    def calculate_discount(subtotal: float, discount_type: str = "nominal", discount_val: float = 0.0) -> float:
        """
        Static Method: Menghitung nilai diskon dalam Rupiah.
        - discount_type = 'percent': discount_val dianggap persen (misal 10 untuk 10%)
        - discount_type = 'nominal': discount_val dianggap nominal rupiah langsung
        """
        sub = float(subtotal)
        val = float(discount_val)
        if val <= 0:
            return 0.0

        if discount_type == "percent":
            if val > 100:
                val = 100.0
            return (val / 100.0) * sub
        else:
            return min(val, sub)

    @staticmethod
    def validate_payment(total: float, cash_paid: float) -> bool:
        """
        Static Method: Memvalidasi apakah uang pembayaran mencukupi total belanja.
        """
        return float(cash_paid) >= float(total)

    @staticmethod
    def generate_invoice_number() -> str:
        """
        Static Method: Menghasilkan kode nomor struk/invoice unik otomatis.
        Format: INV-YYYYMMDD-HHMMSS-XXXX
        """
        now = datetime.now()
        date_str = now.strftime("%Y%m%d%H%M%S")
        import random
        rand_suffix = f"{random.randint(100, 999)}"
        return f"INV-{date_str}-{rand_suffix}"

    # --------------------------------- METHOD ---------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Konversi objek transaksi ke dictionary."""
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "user_id": self.user_id,
            "cashier_name": self.cashier_name,
            "subtotal": self.subtotal,
            "discount": self.discount,
            "total": self.__total,
            "cash_paid": self.__cash_paid,
            "change_amount": self.__change_amount,
            "payment_method": self.payment_method,
            "notes": self.notes,
            "created_at": self.created_at,
            "items_count": len(self.items),
            "items": self.items
        }

    # ------------------------------ CLASS METHOD ------------------------------
    @classmethod
    def from_db_row(cls, row: sqlite3.Row, items: Optional[List[Dict[str, Any]]] = None) -> 'Transaction':
        """Class Method: Membuat objek Transaction dari SQLite Row."""
        if row is None:
            return None
        return cls(
            id=row["id"],
            invoice_number=row["invoice_number"],
            user_id=row["user_id"],
            cashier_name=row["cashier_name"],
            subtotal=row["subtotal"],
            discount=row["discount"],
            total=row["total"],
            cash_paid=row["cash_paid"],
            change_amount=row["change_amount"],
            payment_method=row["payment_method"],
            notes=row["notes"],
            created_at=row["created_at"],
            items=items or []
        )

    @classmethod
    def get_by_id(cls, transaction_id: int) -> Optional['Transaction']:
        """Mengambil data lengkap transaksi beserta rincian itemnya."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        trx_row = cursor.fetchone()
        if not trx_row:
            conn.close()
            return None

        # Ambil rincian detail barang yang dibeli
        cursor.execute("""
            SELECT td.*, p.image AS product_image
            FROM transaction_details td
            LEFT JOIN products p ON td.product_id = p.id
            WHERE td.transaction_id = ?
        """, (transaction_id,))
        detail_rows = cursor.fetchall()
        items = [dict(d) for d in detail_rows]
        conn.close()

        return cls.from_db_row(trx_row, items)

    @classmethod
    def get_by_invoice(cls, invoice_number: str) -> Optional['Transaction']:
        """Mencari transaksi berdasarkan nomor invoice."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM transactions WHERE invoice_number = ?", (invoice_number.strip(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return cls.get_by_id(row["id"])
        return None

    @classmethod
    def get_all(cls, search: str = "", date_from: str = "", date_to: str = "",
                cashier_name: str = "", limit: int = 200) -> List['Transaction']:
        """Mengambil daftar riwayat transaksi dengan berbagai kriteria filter."""
        conn = db_instance.get_connection()
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if search:
            query += " AND invoice_number LIKE ?"
            params.append(f"%{search}%")
        if date_from:
            query += " AND DATE(created_at) >= DATE(?)"
            params.append(date_from)
        if date_to:
            query += " AND DATE(created_at) <= DATE(?)"
            params.append(date_to)
        if cashier_name:
            query += " AND cashier_name LIKE ?"
            params.append(f"%{cashier_name}%")

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [cls.from_db_row(row) for row in rows]
