from typing import Dict
from flask import Blueprint, render_template, request, jsonify, session
from routes.auth import login_required
from models.product import Product
from models.category import Category
from models.cart import Cart
from models.cashier import Cashier
from models.transaction import Transaction
from models.database import db_instance

cashier_bp = Blueprint('cashier', __name__)

# Penyimpanan objek Cart aktif per session user (In-Memory OOP Instances)
active_carts: Dict[int, Cart] = {}

def get_user_cart() -> Cart:
    """Mengambil atau menginisialisasi objek Cart OOP untuk user yang sedang aktif."""
    user_id = session.get('user_id', 0)
    if user_id not in active_carts:
        active_carts[user_id] = Cart()
    return active_carts[user_id]

@cashier_bp.route('/pos')
@cashier_bp.route('/cashier')
@login_required
def pos_screen():
    """Halaman Utama Antarmuka Kasir / Point of Sale."""
    categories = Category.get_all()
    products = Product.get_all()
    return render_template('cashier.html', categories=categories, products=products)

# ==============================================================================
# API ENDPOINTS UNTUK TRANSAKSI POS REAL-TIME (AJAX)
# ==============================================================================

@cashier_bp.route('/api/pos/products', methods=['GET'])
@login_required
def api_get_products():
    """Mendapatkan daftar produk dengan filter pencarian dan kategori."""
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    products = Product.get_all(search=search, category_id=category_id)
    return jsonify({
        "status": "success",
        "products": [p.to_dict() for p in products]
    })

@cashier_bp.route('/api/pos/cart', methods=['GET'])
@login_required
def api_get_cart():
    """Mengambil status keranjang belanja saat ini."""
    cart = get_user_cart()
    return jsonify({
        "status": "success",
        "cart": cart.to_dict()
    })

@cashier_bp.route('/api/pos/cart/add', methods=['POST'])
@login_required
def api_cart_add():
    """Menambahkan produk ke keranjang belanja (bisa via klik produk atau scan barcode)."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    code = data.get('code')
    quantity = int(data.get('quantity', 1))

    product = None
    if product_id:
        product = Product.get_by_id(int(product_id))
    elif code:
        product = Product.get_by_code(str(code))

    if not product:
        return jsonify({"status": "error", "message": "Produk tidak ditemukan."}), 404

    cart = get_user_cart()
    try:
        cart.add_item(product, quantity)
        return jsonify({
            "status": "success",
            "message": f"'{product.name}' berhasil ditambahkan ke keranjang.",
            "cart": cart.to_dict()
        })
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@cashier_bp.route('/api/pos/cart/update', methods=['POST'])
@login_required
def api_cart_update():
    """Mengubah kuantitas item di keranjang belanja."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    if not product_id:
        return jsonify({"status": "error", "message": "Product ID diperlukan."}), 400

    cart = get_user_cart()
    try:
        cart.update_quantity(int(product_id), quantity)
        return jsonify({
            "status": "success",
            "message": "Kuantitas berhasil diperbarui.",
            "cart": cart.to_dict()
        })
    except (ValueError, KeyError) as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@cashier_bp.route('/api/pos/cart/remove', methods=['POST'])
@login_required
def api_cart_remove():
    """Menghapus satu item dari keranjang."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({"status": "error", "message": "Product ID diperlukan."}), 400

    cart = get_user_cart()
    cart.remove_item(int(product_id))
    return jsonify({
        "status": "success",
        "message": "Item berhasil dihapus dari keranjang.",
        "cart": cart.to_dict()
    })

@cashier_bp.route('/api/pos/cart/clear', methods=['POST'])
@login_required
def api_cart_clear():
    """Mengosongkan keranjang belanja kasir."""
    cart = get_user_cart()
    cart.clear()
    return jsonify({
        "status": "success",
        "message": "Keranjang belanja telah dikosongkan.",
        "cart": cart.to_dict()
    })

@cashier_bp.route('/api/pos/checkout', methods=['POST'])
@login_required
def api_checkout():
    """
    Memproses pembayaran transaksi kasir menggunakan objek Cashier secara ATOMIC.
    """
    data = request.get_json() or {}
    discount_type = data.get('discount_type', 'nominal')  # 'nominal' atau 'percent'
    discount_val = float(data.get('discount_val', 0.0))
    cash_paid = float(data.get('cash_paid', 0.0))
    payment_method = data.get('payment_method', 'cash')
    notes = data.get('notes', '')

    cart = get_user_cart()
    if cart.is_empty():
        return jsonify({"status": "error", "message": "Keranjang belanja masih kosong."}), 400

    # Inisialisasi objek Kasir
    user_id = session.get('user_id')
    cashier_name = session.get('full_name', 'Kasir')
    cashier_obj = Cashier(user_id=user_id, cashier_name=cashier_name)

    try:
        # Eksekusi transaksi atomik
        transaction_obj = cashier_obj.process_checkout(
            cart=cart,
            discount_type=discount_type,
            discount_val=discount_val,
            cash_paid=cash_paid,
            payment_method=payment_method,
            notes=notes
        )

        return jsonify({
            "status": "success",
            "message": "Transaksi berhasil diproses!",
            "transaction": transaction_obj.to_dict()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@cashier_bp.route('/pos/receipt/<int:trx_id>')
@login_required
def view_receipt(trx_id: int):
    """Menampilkan halaman struk pembelian kasir khusus cetak thermal printer."""
    trx = Transaction.get_by_id(trx_id)
    if not trx:
        return "Transaksi tidak ditemukan", 404

    # Ambil info toko
    conn = db_instance.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings LIMIT 1")
    store_setting = cursor.fetchone()
    conn.close()

    paper_width = request.args.get('paper', '58')  # 58mm atau 80mm
    return render_template('receipt_thermal.html', trx=trx, store=store_setting, paper_width=paper_width)
