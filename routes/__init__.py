from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.products import products_bp
from routes.categories import categories_bp
from routes.cashier import cashier_bp
from routes.transactions import transactions_bp
from routes.reports import reports_bp
from routes.settings import settings_bp
from routes.users import users_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'products_bp',
    'categories_bp',
    'cashier_bp',
    'transactions_bp',
    'reports_bp',
    'settings_bp',
    'users_bp'
]
