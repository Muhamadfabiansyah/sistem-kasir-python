import io
from flask import Blueprint, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from routes.auth import login_required
from models.transaction import Transaction
from models.database import db_instance

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/transactions')
@login_required
def index():
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    cashier = request.args.get('cashier', '').strip()

    transactions = Transaction.get_all(
        search=search,
        date_from=date_from,
        date_to=date_to,
        cashier_name=cashier
    )

    # Ambil daftar nama kasir unik untuk filter dropdown
    conn = db_instance.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT cashier_name FROM transactions ORDER BY cashier_name ASC")
    cashier_list = [r["cashier_name"] for r in cursor.fetchall()]
    conn.close()

    return render_template(
        'transactions.html',
        transactions=transactions,
        cashier_list=cashier_list,
        search=search,
        date_from=date_from,
        date_to=date_to,
        selected_cashier=cashier
    )

@transactions_bp.route('/api/transactions/<int:trx_id>')
@login_required
def api_detail(trx_id: int):
    trx = Transaction.get_by_id(trx_id)
    if not trx:
        return jsonify({"status": "error", "message": "Transaksi tidak ditemukan."}), 404
    return jsonify({"status": "success", "transaction": trx.to_dict()})

@transactions_bp.route('/transactions/<int:trx_id>/pdf')
@login_required
def download_pdf(trx_id: int):
    """Membuat dan mengunduh berkas PDF struk menggunakan reportlab."""
    trx = Transaction.get_by_id(trx_id)
    if not trx:
        return "Transaksi tidak ditemukan", 404

    conn = db_instance.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings LIMIT 1")
    store = cursor.fetchone()
    conn.close()

    buffer = io.BytesIO()
    # Gunakan ukuran struk custom
    p = canvas.Canvas(buffer, pagesize=(220, 400 + (len(trx.items) * 35)))
    width, height = 220, 400 + (len(trx.items) * 35)

    y = height - 30
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width / 2.0, y, store["store_name"] if store else "TOKO KASIR")
    y -= 15
    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2.0, y, store["store_address"] if store else "")
    y -= 12
    p.drawCentredString(width / 2.0, y, f"Telp: {store['store_phone']}" if store else "")
    y -= 15
    p.line(10, y, width - 10, y)
    y -= 15

    p.setFont("Helvetica", 8)
    p.drawString(10, y, f"No: {trx.invoice_number}")
    y -= 12
    p.drawString(10, y, f"Kasir: {trx.cashier_name}")
    y -= 12
    p.drawString(10, y, f"Waktu: {trx.created_at}")
    y -= 15
    p.line(10, y, width - 10, y)
    y -= 15

    for item in trx.items:
        p.setFont("Helvetica-Bold", 8)
        p.drawString(10, y, item["product_name"][:22])
        y -= 12
        p.setFont("Helvetica", 8)
        sub_str = f"Rp{int(item['subtotal']):,}".replace(",", ".")
        p.drawString(15, y, f"{item['quantity']} x Rp{int(item['price']):,}".replace(",", "."))
        p.drawRightString(width - 10, y, sub_str)
        y -= 15

    p.line(10, y, width - 10, y)
    y -= 15

    def draw_row(label, val_str):
        nonlocal y
        p.drawString(10, y, label)
        p.drawRightString(width - 10, y, val_str)
        y -= 14

    draw_row("Subtotal:", f"Rp{int(trx.subtotal):,}".replace(",", "."))
    draw_row("Diskon:", f"Rp{int(trx.discount):,}".replace(",", "."))
    p.setFont("Helvetica-Bold", 9)
    draw_row("TOTAL:", f"Rp{int(trx.total):,}".replace(",", "."))
    p.setFont("Helvetica", 8)
    draw_row("Bayar:", f"Rp{int(trx.cash_paid):,}".replace(",", "."))
    draw_row("Kembalian:", f"Rp{int(trx.change_amount):,}".replace(",", "."))

    y -= 10
    p.line(10, y, width - 10, y)
    y -= 20
    p.setFont("Helvetica-Oblique", 7)
    p.drawCentredString(width / 2.0, y, "Terima Kasih Atas Kunjungan Anda")

    p.showPage()
    p.save()
    buffer.seek(0)

    filename = f"Struk_{trx.invoice_number}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
