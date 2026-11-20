from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.auth import login_required, admin_required
from models.category import Category

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories')
@login_required
@admin_required
def index():
    categories = Category.get_all()
    return render_template('categories.html', categories=categories)

@categories_bp.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash("Nama kategori wajib diisi.", "danger")
        return redirect(url_for('categories.index'))

    try:
        Category.create(name=name, description=description)
        flash(f"Kategori '{name}' berhasil ditambahkan.", "success")
    except Exception as e:
        flash(f"Gagal menambah kategori: {str(e)}", "danger")

    return redirect(url_for('categories.index'))

@categories_bp.route('/categories/edit/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def edit(category_id: int):
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash("Nama kategori wajib diisi.", "danger")
        return redirect(url_for('categories.index'))

    try:
        Category.update(category_id=category_id, name=name, description=description)
        flash(f"Kategori '{name}' berhasil diperbarui.", "success")
    except Exception as e:
        flash(f"Gagal memperbarui kategori: {str(e)}", "danger")

    return redirect(url_for('categories.index'))

@categories_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete(category_id: int):
    cat = Category.get_by_id(category_id)
    if not cat:
        flash("Kategori tidak ditemukan.", "danger")
        return redirect(url_for('categories.index'))

    if Category.delete(category_id):
        flash(f"Kategori '{cat.name}' berhasil dihapus.", "success")
    else:
        flash("Gagal menghapus kategori.", "danger")

    return redirect(url_for('categories.index'))
