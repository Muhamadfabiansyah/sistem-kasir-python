import os
from flask import Flask, redirect, url_for, session, render_template
from config import config_by_name
from models.database import db_instance
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.cashier import cashier_bp
from routes.products import products_bp
from routes.categories import categories_bp
from routes.transactions import transactions_bp
from routes.reports import reports_bp
from routes.settings import settings_bp
from routes.users import users_bp

def create_app(config_name=None):
    """Factory function untuk membuat instance aplikasi Flask."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Inisialisasi Database SQLite & Tabel Secara Otomatis
    with app.app_context():
        db_instance.init_db()

    # Custom Jinja Filter
    @app.template_filter('format_rupiah')
    def format_rupiah_filter(value):
        try:
            val = int(round(float(value)))
            return f"Rp{val:,}".replace(",", ".")
        except (ValueError, TypeError):
            return "Rp0"

    # Registrasi Seluruh Blueprint Modul
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(cashier_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(users_bp)

    # Route Root (/)
    @app.route('/')
    def root():
        if 'user_id' in session:
            if session.get('user_role') == 'admin':
                return redirect(url_for('dashboard.index'))
            return redirect(url_for('cashier.pos_screen'))
        return redirect(url_for('auth.login'))

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('base.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
