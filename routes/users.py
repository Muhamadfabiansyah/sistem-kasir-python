from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.auth import login_required, admin_required
from models.user import User

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@login_required
@admin_required
def index():
    users = User.get_all()
    return render_template('users.html', users=users)

@users_bp.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add():
    username = request.form.get('username', '').strip().lower()
    full_name = request.form.get('full_name', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'cashier').strip().lower()

    if not username or not full_name or not password:
        flash("Seluruh field wajib diisi.", "danger")
        return redirect(url_for('users.index'))

    try:
        User.create(username=username, password=password, full_name=full_name, role=role)
        flash(f"Pengguna '{full_name}' ({username}) berhasil ditambahkan.", "success")
    except ValueError as e:
        flash(f"Gagal menambahkan pengguna: {str(e)}", "danger")

    return redirect(url_for('users.index'))

@users_bp.route('/users/edit/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit(user_id: int):
    full_name = request.form.get('full_name', '').strip()
    role = request.form.get('role', 'cashier').strip().lower()
    new_password = request.form.get('new_password', '').strip()

    if not full_name:
        flash("Nama lengkap wajib diisi.", "danger")
        return redirect(url_for('users.index'))

    try:
        User.update(user_id=user_id, full_name=full_name, role=role, new_password=new_password or None)
        flash(f"Data pengguna '{full_name}' berhasil diperbarui.", "success")
    except ValueError as e:
        flash(f"Gagal memperbarui pengguna: {str(e)}", "danger")

    return redirect(url_for('users.index'))

@users_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete(user_id: int):
    # Cegah admin menghapus dirinya sendiri
    if user_id == session.get('user_id'):
        flash("Anda tidak dapat menghapus akun Anda sendiri yang sedang aktif!", "danger")
        return redirect(url_for('users.index'))

    target = User.get_by_id(user_id)
    if not target:
        flash("Pengguna tidak ditemukan.", "danger")
        return redirect(url_for('users.index'))

    if User.delete(user_id):
        flash(f"Akun pengguna '{target.full_name}' berhasil dihapus.", "success")
    else:
        flash("Gagal menghapus akun pengguna.", "danger")

    return redirect(url_for('users.index'))
