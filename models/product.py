import sqlite3
from typing import Optional, List, Dict, Any
from models.database import db_instance

class Product:
    """
    Class Product merepresentasikan entitas produk/barang dalam sistem POS.
    Menerapkan:
    - Encapsulation: Atribut private __price, __cost_price, __stock
    - Property & Setter dengan validasi ketat
    - Class Method untuk instansiasi dari data row database
    - Method operasional stok
    """

    def __init__(self, id: Optional[int], code: str, name: str, category_id: Optional[int],
                 cost_price: float, price: float, stock: int, image: Optional[str] = None,
                 description: Optional[str] = None, category_name: Optional[str] = None):
        self.id = id
        self.code = code.upper().strip()
        self.name = name.strip()
        self.category_id = category_id
        self.category_name = category_name or "Tanpa Kategori"
        self.image = image or "default-product.png"
        self.description = description or ""

        # Atribut Private (Encapsulation)
        self.__cost_price = 0.0
        self.__price = 0.0
        self.__stock = 0

        # Gunakan setter untuk mengaktifkan validasi
        self.cost_price = cost_price
        self.price = price
        self.stock = stock

    # ----------------------------- PROPERTY & SETTER --------------------------
    @property
    def cost_price(self) -> float:
        """Getter harga beli / modal"""
        return self.__cost_price

    @cost_price.setter
    def cost_price(self, value: float):
        """Setter harga beli dengan validasi >= 0"""
        val = float(value)
        if val < 0:
            raise ValueError("Harga modal tidak boleh negatif.")
        self.__cost_price = val

    @property
    def price(self) -> float:
        """Getter harga jual produk"""
        return self.__price

    @price.setter
    def price(self, value: float):
        """Setter harga jual dengan validasi >= 0"""
        val = float(value)
        if val < 0:
            raise ValueError("Harga jual tidak boleh negatif.")
        self.__price = val

    @property
    def stock(self) -> int:
        """Getter jumlah stok produk"""
        return self.__stock

    @stock.setter
    def stock(self, value: int):
        """Setter jumlah stok dengan validasi >= 0"""
        val = int(value)
        if val < 0:
            raise ValueError("Jumlah stok tidak boleh negatif.")
        self.__stock = val

    # --------------------------------- METHOD ---------------------------------
    def decrease_stock(self, quantity: int) -> bool:
        """Mengurangi stok barang dengan validasi stok mencukupi."""
        if quantity <= 0:
            raise ValueError("Jumlah pengurangan stok harus lebih dari 0.")
        if quantity > self.__stock:
            raise ValueError(f"Stok '{self.name}' tidak mencukupi (Tersisa {self.__stock}).")
        
        self.__stock -= quantity
        return True

    def increase_stock(self, quantity: int) -> bool:
        """Menambah stok barang."""
        if quantity <= 0:
            raise ValueError("Jumlah penambahan stok harus lebih dari 0.")
        self.__stock += quantity
        return True

    def is_in_stock(self, quantity: int = 1) -> bool:
        """Cek ketersediaan stok"""
        return self.__stock >= quantity

    def to_dict(self) -> Dict[str, Any]:
        """Konversi objek produk ke dictionary untuk JSON / API"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "cost_price": self.__cost_price,
            "price": self.__price,
            "stock": self.__stock,
            "image": self.image,
            "description": self.description,
            "is_low_stock": self.__stock <= 5,
            "is_out_of_stock": self.__stock == 0
        }

    # ------------------------------ CLASS METHOD ------------------------------
    @classmethod
    def from_db_row(cls, row: sqlite3.Row):
        """Class Method: Membuat objek Product langsung dari row SQLite."""
        if row is None:
            return None
        cat_name = row["category_name"] if "category_name" in row.keys() else None
        return cls(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            category_id=row["category_id"],
            cost_price=row["cost_price"],
            price=row["price"],
            stock=row["stock"],
            image=row["image"],
            description=row["description"],
            category_name=cat_name
        )

    # ----------------------- DATABASE ACCESS METHODS -------------------------
    @classmethod
    def get_all(cls, search: str = "", category_id: Optional[int] = None) -> List['Product']:
        """Mengambil seluruh daftar produk dari database dengan filter opsional."""
        conn = db_instance.get_connection()
        query = """
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (p.name LIKE ? OR p.code LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        
        query += " ORDER BY p.id DESC"
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [cls.from_db_row(row) for row in rows]

    @classmethod
    def get_by_id(cls, product_id: int) -> Optional['Product']:
        """Mendapatkan data produk berdasarkan ID."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        """, (product_id,))
        row = cursor.fetchone()
        conn.close()
        return cls.from_db_row(row) if row else None

    @classmethod
    def get_by_code(cls, code: str) -> Optional['Product']:
        """Mendapatkan data produk berdasarkan Barcode / Kode Produk."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE UPPER(p.code) = UPPER(?)
        """, (code.strip(),))
        row = cursor.fetchone()
        conn.close()
        return cls.from_db_row(row) if row else None

    @classmethod
    def create(cls, code: str, name: str, category_id: Optional[int],
               cost_price: float, price: float, stock: int,
               image: Optional[str] = None, description: Optional[str] = None) -> 'Product':
        """Menyimpan produk baru ke database."""
        # Validasi melalui inisialisasi objek sementara
        temp = cls(None, code, name, category_id, cost_price, price, stock, image, description)
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (code, name, category_id, cost_price, price, stock, image, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (temp.code, temp.name, temp.category_id, temp.cost_price, temp.price, temp.stock, temp.image, temp.description))
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return cls.get_by_id(product_id)

    @classmethod
    def update(cls, product_id: int, code: str, name: str, category_id: Optional[int],
               cost_price: float, price: float, stock: int,
               image: Optional[str] = None, description: Optional[str] = None) -> bool:
        """Memperbarui data produk yang tersimpan."""
        # Validasi
        temp = cls(product_id, code, name, category_id, cost_price, price, stock, image, description)
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        if image:
            cursor.execute("""
                UPDATE products 
                SET code = ?, name = ?, category_id = ?, cost_price = ?, price = ?, stock = ?, image = ?, description = ?
                WHERE id = ?
            """, (temp.code, temp.name, temp.category_id, temp.cost_price, temp.price, temp.stock, temp.image, temp.description, product_id))
        else:
            cursor.execute("""
                UPDATE products 
                SET code = ?, name = ?, category_id = ?, cost_price = ?, price = ?, stock = ?, description = ?
                WHERE id = ?
            """, (temp.code, temp.name, temp.category_id, temp.cost_price, temp.price, temp.stock, temp.description, product_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    @classmethod
    def delete(cls, product_id: int) -> bool:
        """Menghapus produk dari database."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    @classmethod
    def generate_next_code(cls) -> str:
        """Membuat kode produk unik otomatis (format: PRD-XXX)."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM products")
        max_id = cursor.fetchone()[0] or 0
        conn.close()
        return f"PRD-{(max_id + 1):03d}"
