from typing import Dict, Any, Optional
from models.product import Product

class Cart:
    """
    Class Cart mengelola keranjang belanja pengguna/kasir pada sesi POS.
    Menerapkan:
    - Encapsulation: Atribut private __items untuk menjaga integritas keranjang
    - Property items untuk akses terkontrol
    - Method penambahan, penghapusan, kalkulasi total dengan validasi stok
    """

    def __init__(self):
        # Atribut Private: { product_id: {"product": Product, "quantity": int, "subtotal": float} }
        self.__items: Dict[int, Dict[str, Any]] = {}

    @property
    def items(self) -> Dict[int, Dict[str, Any]]:
        """Getter untuk membaca dictionary daftar item di keranjang"""
        return self.__items

    def add_item(self, product: Product, quantity: int = 1) -> bool:
        """
        Menambahkan produk ke keranjang atau menambah jumlah jika sudah ada.
        Memvalidasi agar akumulasi jumlah tidak melampaui stok yang tersedia.
        """
        if quantity <= 0:
            raise ValueError("Kuantitas produk yang ditambahkan harus lebih dari 0.")

        product_id = product.id
        current_qty = self.__items[product_id]["quantity"] if product_id in self.__items else 0
        total_requested = current_qty + quantity

        if total_requested > product.stock:
            raise ValueError(f"Stok '{product.name}' tidak mencukupi! Tersedia: {product.stock}, diminta: {total_requested}.")

        if product_id in self.__items:
            self.__items[product_id]["quantity"] = total_requested
            self.__items[product_id]["subtotal"] = total_requested * product.price
        else:
            self.__items[product_id] = {
                "product": product,
                "quantity": total_requested,
                "price": product.price,
                "cost_price": product.cost_price,
                "subtotal": total_requested * product.price
            }
        return True

    def update_quantity(self, product_id: int, quantity: int) -> bool:
        """Mengubah kuantitas item tertentu di keranjang dengan validasi stok."""
        if product_id not in self.__items:
            raise KeyError("Produk tidak ditemukan di keranjang belanja.")

        if quantity <= 0:
            return self.remove_item(product_id)

        product: Product = self.__items[product_id]["product"]
        if quantity > product.stock:
            raise ValueError(f"Stok tidak mencukupi! Maksimal {product.stock} pcs.")

        self.__items[product_id]["quantity"] = quantity
        self.__items[product_id]["subtotal"] = quantity * product.price
        return True

    def remove_item(self, product_id: int) -> bool:
        """Menghapus item tertentu dari keranjang."""
        if product_id in self.__items:
            del self.__items[product_id]
            return True
        return False

    def calculate_subtotal(self) -> float:
        """Menghitung total harga sebelum diskon."""
        return sum(item["subtotal"] for item in self.__items.values())

    def clear(self):
        """Mengosongkan keranjang belanja."""
        self.__items.clear()

    def is_empty(self) -> bool:
        """Mengecek apakah keranjang kosong."""
        return len(self.__items) == 0

    def count_items(self) -> int:
        """Menghitung total kuantitas seluruh produk di keranjang."""
        return sum(item["quantity"] for item in self.__items.values())

    def to_dict(self) -> Dict[str, Any]:
        """Konversi keranjang ke bentuk dictionary (berguna untuk API / JSON respons)."""
        items_list = []
        for pid, data in self.__items.items():
            prod: Product = data["product"]
            items_list.append({
                "product_id": pid,
                "code": prod.code,
                "name": prod.name,
                "price": prod.price,
                "quantity": data["quantity"],
                "stock": prod.stock,
                "subtotal": data["subtotal"],
                "image": prod.image
            })
        
        subtotal = self.calculate_subtotal()
        return {
            "items": items_list,
            "total_items": self.count_items(),
            "total_unique": len(self.__items),
            "subtotal": subtotal
        }
