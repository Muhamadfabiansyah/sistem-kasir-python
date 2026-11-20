from datetime import datetime, timedelta
from flask import Blueprint, render_template, session
from routes.auth import login_required, admin_required
from models.database import db_instance

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
@admin_required
def index():
    conn = db_instance.get_connection()
    cursor = conn.cursor()

    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Total Penjualan Hari Ini & Jumlah Transaksi Hari Ini
    cursor.execute("""
        SELECT COUNT(id) AS trx_count, COALESCE(SUM(total), 0) AS total_sales
        FROM transactions
        WHERE DATE(created_at) = DATE(?)
    """, (today_str,))
    today_stat = cursor.fetchone()
    today_trx_count = today_stat["trx_count"]
    today_sales = today_stat["total_sales"]

    # 2. Total Keseluruhan Pendapatan & Transaksi
    cursor.execute("""
        SELECT COUNT(id) AS total_trx, COALESCE(SUM(total), 0) AS total_revenue
        FROM transactions
    """)
    all_stat = cursor.fetchone()
    total_revenue = all_stat["total_revenue"]
    total_trx = all_stat["total_trx"]

    # 3. Jumlah Produk & Stok Menipis
    cursor.execute("SELECT COUNT(id) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(id) FROM products WHERE stock <= 5")
    low_stock_count = cursor.fetchone()[0]

    # 4. Transaksi Terbaru (5 transaksi terakhir)
    cursor.execute("""
        SELECT * FROM transactions
        ORDER BY id DESC LIMIT 5
    """)
    recent_transactions = cursor.fetchall()

    # 5. Produk Terlaris (Top 5 Best Seller)
    cursor.execute("""
        SELECT td.product_name, SUM(td.quantity) AS total_qty, SUM(td.subtotal) AS total_nominal
        FROM transaction_details td
        GROUP BY td.product_name
        ORDER BY total_qty DESC
        LIMIT 5
    """)
    top_products = cursor.fetchall()

    # 6. Data Grafik Penjualan 7 Hari Terakhir
    chart_dates = []
    chart_sales = []
    chart_trx_counts = []

    for i in range(6, -1, -1):
        day_date = datetime.now() - timedelta(days=i)
        day_str = day_date.strftime("%Y-%m-%d")
        day_label = day_date.strftime("%d %b")
        chart_dates.append(day_label)

        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) AS sales, COUNT(id) AS trx
            FROM transactions
            WHERE DATE(created_at) = DATE(?)
        """, (day_str,))
        row = cursor.fetchone()
        chart_sales.append(row["sales"])
        chart_trx_counts.append(row["trx"])

    # 7. Data Grafik Penjualan Berdasarkan Kategori
    cursor.execute("""
        SELECT COALESCE(c.name, 'Lainnya') AS category_name, SUM(td.quantity) AS total_qty
        FROM transaction_details td
        LEFT JOIN products p ON td.product_id = p.id
        LEFT JOIN categories c ON p.category_id = c.id
        GROUP BY category_name
        ORDER BY total_qty DESC
        LIMIT 6
    """)
    cat_rows = cursor.fetchall()
    cat_labels = [r["category_name"] for r in cat_rows]
    cat_values = [r["total_qty"] for r in cat_rows]

    conn.close()

    return render_template(
        'dashboard.html',
        today_sales=today_sales,
        today_trx_count=today_trx_count,
        total_revenue=total_revenue,
        total_products=total_products,
        low_stock_count=low_stock_count,
        recent_transactions=recent_transactions,
        top_products=top_products,
        chart_dates=chart_dates,
        chart_sales=chart_sales,
        chart_trx_counts=chart_trx_counts,
        cat_labels=cat_labels,
        cat_values=cat_values
    )
