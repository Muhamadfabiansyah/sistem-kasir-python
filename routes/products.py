import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from routes.auth import login_required, admin_required
from models.product import Product
from models.category import Category
from config import Config

products_bp = Blueprint('products', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@products_bp.route('/products')
@login_required
@admin_required
def index():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    
    products = Product.get_all(search=search, category_id=category_id)
    categories = Category.get_all()
    next_code = Product.generate_next_code()

    return render_template(
        'products.html',
        products=products,
        categories=categories,
        search=search,
        selected_category=category_id,
        next_code=next_code
    )

@products_bp.route('/products/add', methods=['POST'])
@login_required
@admin_required
def add():
    code = request.form.get('code', '').strip().upper()
    name = request.form.get('name', '').strip()
    category_id = request.form.get('category_id', type=int)
    cost_price = request.form.get('cost_price', type=float, default=0.0)
    price = request.form.get('price', type=float, default=0.0)
    stock = request.form.get('stock', type=int, default=0)
    description = request.form.get('description', '').strip()

    if not code or not name:
        flash("Kode produk dan Nama produk wajib diisi.", "danger")
        return redirect(url_for('products.index'))

    # Cek kode duplikat
    if Product.get_by_code(code):
        flash(f"Produk dengan kode '{code}' sudah ada! Gunakan kode lain.", "danger")
        return redirect(url_for('products.index'))

    # Handle Upload Gambar
    image_filename = "default-product.png"
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            safe_name = f"prod_{code}_{int(os.times().system * 1000)}.{ext}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, safe_name)
            file.save(filepath)
            image_filename = safe_name

    try:
        Product.create(
            code=code,
            name=name,
            category_id=category_id,
            cost_price=cost_price,
            price=price,
            stock=stock,
            image=image_filename,
            description=description
        )
        flash(f"Produk '{name}' berhasil ditambahkan ke katalog.", "success")
    except ValueError as e:
        flash(f"Gagal menambah produk: {str(e)}", "danger")

    return redirect(url_for('products.index'))

@products_bp.route('/products/edit/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def edit(product_id: int):
    prod = Product.get_by_id(product_id)
    if not prod:
        flash("Produk tidak ditemukan.", "danger")
        return redirect(url_for('products.index'))

    code = request.form.get('code', '').strip().upper()
    name = request.form.get('name', '').strip()
    category_id = request.form.get('category_id', type=int)
    cost_price = request.form.get('cost_price', type=float, default=0.0)
    price = request.form.get('price', type=float, default=0.0)
    stock = request.form.get('stock', type=int, default=0)
    description = request.form.get('description', '').strip()

    # Cek jika kode diubah dan kode baru sudah dipakai produk lain
    existing = Product.get_by_code(code)
    if existing and existing.id != product_id:
        flash(f"Kode '{code}' sudah dipakai oleh produk lain.", "danger")
        return redirect(url_for('products.index'))

    # Handle Upload Gambar baru jika ada
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            safe_name = f"prod_{code}_{int(os.times().system * 1000)}.{ext}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, safe_name)
            file.save(filepath)
            image_filename = safe_name

    try:
        Product.update(
            product_id=product_id,
            code=code,
            name=name,
            category_id=category_id,
            cost_price=cost_price,
            price=price,
            stock=stock,
            image=image_filename,
            description=description
        )
        flash(f"Data produk '{name}' berhasil diperbarui.", "success")
    except ValueError as e:
        flash(f"Gagal memperbarui produk: {str(e)}", "danger")

    return redirect(url_for('products.index'))

@products_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete(product_id: int):
    prod = Product.get_by_id(product_id)
    if not prod:
        flash("Produk tidak ditemukan.", "danger")
        return redirect(url_for('products.index'))

    if Product.delete(product_id):
        flash(f"Produk '{prod.name}' berhasil dihapus.", "success")
    else:
        flash("Gagal menghapus produk.", "danger")

    return redirect(url_for('products.index'))

@products_bp.route('/api/products/next-code')
@login_required
@admin_required
def api_next_code():
    return jsonify({"next_code": Product.generate_next_code()})
