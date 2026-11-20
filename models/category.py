import sqlite3
from typing import Optional, List, Dict, Any
from models.database import db_instance

class Category:
    """
    Class Category merepresentasikan kategori produk untuk pengelompokan barang.
    """

    def __init__(self, id: Optional[int], name: str, description: Optional[str] = None,
                 product_count: int = 0):
        self.id = id
        self.name = name.strip()
        self.description = description or ""
        self.product_count = product_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "product_count": self.product_count
        }

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> Optional['Category']:
        if row is None:
            return None
        count = row["product_count"] if "product_count" in row.keys() else 0
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            product_count=count
        )

    @classmethod
    def get_all(cls) -> List['Category']:
        """Mengambil seluruh kategori beserta jumlah produk masing-masing."""
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, COUNT(p.id) AS product_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            GROUP BY c.id
            ORDER BY c.name ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [cls.from_db_row(r) for r in rows]

    @classmethod
    def get_by_id(cls, category_id: int) -> Optional['Category']:
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        row = cursor.fetchone()
        conn.close()
        return cls.from_db_row(row)

    @classmethod
    def create(cls, name: str, description: Optional[str] = None) -> 'Category':
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Nama kategori tidak boleh kosong.")
        
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO categories (name, description) VALUES (?, ?)
        """, (clean_name, description.strip() if description else ""))
        cid = cursor.lastrowid
        conn.commit()
        conn.close()
        return cls.get_by_id(cid)

    @classmethod
    def update(cls, category_id: int, name: str, description: Optional[str] = None) -> bool:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Nama kategori tidak boleh kosong.")
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE categories SET name = ?, description = ? WHERE id = ?
        """, (clean_name, description.strip() if description else "", category_id))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    @classmethod
    def delete(cls, category_id: int) -> bool:
        conn = db_instance.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
