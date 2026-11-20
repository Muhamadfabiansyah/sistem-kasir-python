from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.auth import login_required, admin_required, get_current_user
from models.user import User
from models.database import db_instance

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def index():
    conn = db_instance.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings LIMIT 1")
    store = cursor.fetchone()
    conn.close()

    current_user = get_current_user()
    return render_template('settings.html', store=store, current_user=current_user)

@settings_bp.route('/settings/store', methods=['POST'])
@login_required
@admin_required
def update_store():
    store_name = request.form.get('store_name', '').strip()
    store_address = request.form.get('store_address', '').strip()
    store_phone = request.form.get('store_phone', '').strip()
    receipt_footer = request.form.get('receipt_footer', '').strip()

    if not store_name:
        flash("Nama toko tidak boleh kosong.", "danger")
        return redirect(url_for('settings.index'))

    conn = db_instance.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE settings
        SET store_name = ?, store_address = ?, store_phone = ?, receipt_footer = ?
        WHERE id = 1
    """, (store_name, store_address, store_phone, receipt_footer))
    conn.commit()
    conn.close()

    flash("Informasi toko berhasil diperbarui.", "success")
    return redirect(url_for('settings.index'))

@settings_bp.route('/settings/password', methods=['POST'])
@login_required
def change_password():
    user = get_current_user()
    current_pass = request.form.get('current_password', '')
    new_pass = request.form.get('new_password', '')
    confirm_pass = request.form.get('confirm_password', '')

    if not user.check_password(current_pass):
        flash("Password lama yang Anda masukkan salah.", "danger")
        return redirect(url_for('settings.index'))

    if len(new_pass) < 4:
        flash("Password baru minimal 4 karakter.", "danger")
        return redirect(url_for('settings.index'))

    if new_pass != confirm_pass:
        flash("Konfirmasi password baru tidak cocok.", "danger")
        return redirect(url_for('settings.index'))

    user.set_password(new_pass)
    conn = db_instance.get_connection()
    cursor = conn.cursor()
    # update via setter hash
    from werkzeug.security import generate_password_hash
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(new_pass), user.id))
    conn.commit()
    conn.close()

    flash("Password berhasil diubah. Silakan gunakan password baru pada login berikutnya.", "success")
    return redirect(url_for('settings.index'))
