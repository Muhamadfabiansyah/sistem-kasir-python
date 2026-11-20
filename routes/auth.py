from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from models.user import User

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Silakan login terlebih dahulu untuk mengakses sistem.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash("Akses ditolak! Halaman ini hanya untuk Administrator.", "danger")
            return redirect(url_for('cashier.pos_screen'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Mengambil objek User dari database berdasarkan session aktif."""
    if 'user_id' in session:
        return User.get_by_id(session['user_id'])
    return None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        # Jika sudah login, arahkan sesuai peran
        if session.get('user_role') == 'admin':
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('cashier.pos_screen'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Username dan password wajib diisi.", "danger")
            return render_template('login.html', username=username)

        user = User.authenticate(username, password)
        if user:
            # Set Session
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name
            session['user_role'] = user.role
            session.permanent = True

            flash(f"Selamat datang kembali, {user.full_name}!", "success")
            next_url = request.args.get('next')
            if next_url and not next_url.startswith('//') and not next_url.startswith('http'):
                return redirect(next_url)

            if user.is_admin():
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('cashier.pos_screen'))
        else:
            flash("Username atau password salah. Silakan coba lagi.", "danger")

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Anda telah berhasil logout dari sistem kasir.", "info")
    return redirect(url_for('auth.login'))
