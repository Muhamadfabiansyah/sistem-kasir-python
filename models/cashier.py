import sqlite3
from typing import Optional, Dict, Any
from models.database import db_instance
from models.cart import Cart
from models.transaction import Transaction
from models.product import Product

class Cashier:
    """
    Class Cashier mengelola seluruh alur operasional kasir:
    - Melakukan validasi pembayaran
    - Memproses checkout secara ATOMIC (Database Transaction)
    - Memastikan stok tidak menjadi negatif (Integritas Data)
    - Mencatat detail transaksi & mengosongkan keranjang
    """

    def __init__(self, user_id: Optional[int], cashier_name: str):
        self.user_id = user_id
        self.__cashier_name = cashier_name.strip() if cashier_name else "Kasir POS"

    @property
    def cashier_name(self) -> str:
        """Getter nama kasir"""
        return self.__cashier_name

    @cashier_name.setter
    def cashier_name(self, value: str):
        if not value or not value.strip():
            raise ValueError("Nama kasir tidak boleh kosong.")
        self.__cashier_name = value.strip()

    def process_checkout(self, cart: Cart, discount_type: str = "nominal",
                         discount_val: float = 0.0, cash_paid: float = 0.0,
                         payment_method: str = "cash", notes: str = "") -> Transaction:
        """
        Memproses transaksi checkout dari keranjang belanja secara ACID (Atomic).
        Jika ada kendala stok atau pembayaran kurang, seluruh transaksi di-rollback.
        """
        if cart.is_empty():
            raise ValueError("Keranjang belanja masih kosong! Tidak dapat memproses transaksi.")

        subtotal = cart.calculate_subtotal()
        discount = Transaction.calculate_discount(subtotal, discount_type, discount_val)
        total = max(0.0, subtotal - discount)

        # Validasi nominal pembayaran
        if not Transaction.validate_payment(total, cash_paid):
            kurang = total - cash_paid
            raise ValueError(f"Uang yang dibayarkan kurang Rp{int(round(kurang)):,}".replace(",", "."))

        change_amount = cash_paid - total
        invoice_number = Transaction.generate_invoice_number()

        # Mulai Atomic Database Transaction
        conn = db_instance.get_connection()
        cursor = conn.cursor()

        try:
            # 1. Simpan header transaksi ke tabel transactions
            cursor.execute("""
                INSERT INTO transactions (
                    invoice_number, user_id, cashier_name, subtotal, discount,
                    total, cash_paid, change_amount, payment_method, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_number, self.user_id, self.__cashier_name, subtotal, discount,
                total, cash_paid, change_amount, payment_method, notes
            ))
            transaction_id = cursor.lastrowid

            # 2. Iterasi setiap barang di keranjang: kurangi stok dan simpan detail
            items_details = []
            for product_id, item_data in cart.items.items():
                qty = item_data["quantity"]
                prod: Product = item_data["product"]

                # Cek stok terkini secara real-time dari database
                cursor.execute("SELECT stock, cost_price, price, name, code FROM products WHERE id = ?", (product_id,))
                prod_row = cursor.fetchone()
                if not prod_row:
                    raise ValueError(f"Produk '{prod.name}' tidak ditemukan di database.")

                current_db_stock = prod_row["stock"]
                cost_price = prod_row["cost_price"]
                actual_price = prod_row["price"]
                item_subtotal = actual_price * qty

                if current_db_stock < qty:
                    raise ValueError(f"Stok '{prod_row['name']}' tidak mencukupi di sistem! Tersisa {current_db_stock}, diminta {qty}.")

                # Simpan ke tabel transaction_details
                cursor.execute("""
                    INSERT INTO transaction_details (
                        transaction_id, product_id, product_code, product_name,
                        cost_price, price, quantity, subtotal
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction_id, product_id, prod_row["code"], prod_row["name"],
                    cost_price, actual_price, qty, item_subtotal
                ))

                # Kurangi stok secara atomic
                cursor.execute("""
                    UPDATE products
                    SET stock = stock - ?
                    WHERE id = ?
                """, (qty, product_id))

                # Update stok di memori objek produk
                prod.decrease_stock(qty)

                items_details.append({
                    "product_id": product_id,
                    "product_code": prod_row["code"],
                    "product_name": prod_row["name"],
                    "price": actual_price,
                    "quantity": qty,
                    "subtotal": item_subtotal
                })

            # Jika semua berhasil, COMMIT database
            conn.commit()

        except Exception as e:
            # Jika ada kesalahan apa pun, ROLLBACK seluruh perubahan
            conn.rollback()
            raise e
        finally:
            conn.close()

        # Kosongkan keranjang belanja kasir
        cart.clear()

        # Buat dan kembalikan objek Transaction yang berhasil
        return Transaction(
            id=transaction_id,
            invoice_number=invoice_number,
            user_id=self.user_id,
            cashier_name=self.__cashier_name,
            subtotal=subtotal,
            discount=discount,
            total=total,
            cash_paid=cash_paid,
            change_amount=change_amount,
            payment_method=payment_method,
            notes=notes,
            items=items_details
        )
