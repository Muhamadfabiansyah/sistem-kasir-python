import io
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, send_file
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from routes.auth import login_required, admin_required
from models.database import db_instance

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
@admin_required
def index():
    period = request.args.get('period', 'today')  # today, week, month, custom
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    today = datetime.now()
    if period == 'today':
        date_from = today.strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")
    elif period == 'week':
        start_week = today - timedelta(days=today.weekday())
        date_from = start_week.strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")
    elif period == 'month':
        date_from = today.strftime("%Y-%m-01")
        date_to = today.strftime("%Y-%m-%d")
    elif period == 'custom':
        if not date_from:
            date_from = today.strftime("%Y-%m-01")
        if not date_to:
            date_to = today.strftime("%Y-%m-%d")

    conn = db_instance.get_connection()
    cursor = conn.cursor()

    # 1. Total Penjualan, Transaksi, Diskon pada rentang tanggal
    cursor.execute("""
        SELECT 
            COUNT(id) AS total_trx,
            COALESCE(SUM(subtotal), 0) AS total_subtotal,
            COALESCE(SUM(discount), 0) AS total_discount,
            COALESCE(SUM(total), 0) AS total_omzet
        FROM transactions
        WHERE DATE(created_at) >= DATE(?) AND DATE(created_at) <= DATE(?)
    """, (date_from, date_to))
    summary = cursor.fetchone()

    # 2. Total Modal / HPP untuk menghitung Laba Kotor
    cursor.execute("""
        SELECT COALESCE(SUM(td.cost_price * td.quantity), 0) AS total_hpp
        FROM transaction_details td
        JOIN transactions t ON td.transaction_id = t.id
        WHERE DATE(t.created_at) >= DATE(?) AND DATE(t.created_at) <= DATE(?)
    """, (date_from, date_to))
    hpp_row = cursor.fetchone()
    total_hpp = hpp_row["total_hpp"]
    gross_profit = summary["total_omzet"] - total_hpp

    # 3. Produk Terlaris pada Periode
    cursor.execute("""
        SELECT 
            td.product_code,
            td.product_name,
            SUM(td.quantity) AS total_qty,
            SUM(td.subtotal) AS total_sales
        FROM transaction_details td
        JOIN transactions t ON td.transaction_id = t.id
        WHERE DATE(t.created_at) >= DATE(?) AND DATE(t.created_at) <= DATE(?)
        GROUP BY td.product_name
        ORDER BY total_qty DESC
        LIMIT 10
    """, (date_from, date_to))
    top_selling = cursor.fetchall()

    # 4. Daftar Transaksi Terperinci pada Periode
    cursor.execute("""
        SELECT * FROM transactions
        WHERE DATE(created_at) >= DATE(?) AND DATE(created_at) <= DATE(?)
        ORDER BY id DESC
    """, (date_from, date_to))
    transactions = cursor.fetchall()

    # 5. Data Grafik Harian
    cursor.execute("""
        SELECT DATE(created_at) AS trx_date, SUM(total) AS daily_total, COUNT(id) AS daily_count
        FROM transactions
        WHERE DATE(created_at) >= DATE(?) AND DATE(created_at) <= DATE(?)
        GROUP BY DATE(created_at)
        ORDER BY trx_date ASC
    """, (date_from, date_to))
    daily_rows = cursor.fetchall()
    chart_dates = [r["trx_date"] for r in daily_rows]
    chart_totals = [r["daily_total"] for r in daily_rows]

    conn.close()

    return render_template(
        'reports.html',
        period=period,
        date_from=date_from,
        date_to=date_to,
        summary=summary,
        total_hpp=total_hpp,
        gross_profit=gross_profit,
        top_selling=top_selling,
        transactions=transactions,
        chart_dates=chart_dates,
        chart_totals=chart_totals
    )

@reports_bp.route('/reports/export/excel')
@login_required
@admin_required
def export_excel():
    date_from = request.args.get('date_from', datetime.now().strftime("%Y-%m-01"))
    date_to = request.args.get('date_to', datetime.now().strftime("%Y-%m-%d"))

    conn = db_instance.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM transactions
        WHERE DATE(created_at) >= DATE(?) AND DATE(created_at) <= DATE(?)
        ORDER BY id ASC
    """, (date_from, date_to))
    trx_rows = cursor.fetchall()
    conn.close()

    # Buat Workbook Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Laporan Penjualan"

    # Styling
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=16, bold=True, color="1E3A8A")
    subtitle_font = Font(name="Calibri", size=11, italic=True)

    ws.merge_cells("A1:H1")
    ws["A1"] = "LAPORAN PENJUALAN - SISTEM KASIR POS"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:H2")
    ws["A2"] = f"Periode: {date_from} s/d {date_to}"
    ws["A2"].font = subtitle_font
    ws["A2"].alignment = Alignment(horizontal="center")

    headers = [
        "No.", "No. Invoice", "Tanggal & Waktu", "Nama Kasir",
        "Subtotal (Rp)", "Diskon (Rp)", "Total Omzet (Rp)", "Metode Bayar"
    ]

    row_num = 4
    for col_num, h_text in enumerate(headers, 1):
        cell = ws.cell(row=row_num, column=col_num, value=h_text)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    total_omzet = 0
    total_diskon = 0

    for idx, row in enumerate(trx_rows, 1):
        row_num += 1
        ws.cell(row=row_num, column=1, value=idx).alignment = Alignment(horizontal="center")
        ws.cell(row=row_num, column=2, value=row["invoice_number"])
        ws.cell(row=row_num, column=3, value=row["created_at"])
        ws.cell(row=row_num, column=4, value=row["cashier_name"])
        ws.cell(row=row_num, column=5, value=row["subtotal"]).number_format = "#,##0"
        ws.cell(row=row_num, column=6, value=row["discount"]).number_format = "#,##0"
        ws.cell(row=row_num, column=7, value=row["total"]).number_format = "#,##0"
        ws.cell(row=row_num, column=8, value=row["payment_method"].upper())
        total_omzet += row["total"]
        total_diskon += row["discount"]

    # Baris Total
    row_num += 1
    ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=4)
    ws.cell(row=row_num, column=1, value="TOTAL KESELURUHAN").font = Font(bold=True)
    ws.cell(row=row_num, column=6, value=total_diskon).font = Font(bold=True)
    ws.cell(row=row_num, column=6).number_format = "#,##0"
    ws.cell(row=row_num, column=7, value=total_omzet).font = Font(bold=True)
    ws.cell(row=row_num, column=7).number_format = "#,##0"

    # Atur lebar kolom
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    filename = f"Laporan_Penjualan_{date_from}_sd_{date_to}.xlsx"
    return send_file(buffer, as_attachment=True, download_name=filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@reports_bp.route('/reports/export/pdf')
@login_required
@admin_required
def export_pdf():
    date_from = request.args.get('date_from', datetime.now().strftime("%Y-%m-01"))
    date_to = request.args.get('date_to', datetime.now().strftime("%Y-%m-%d"))

    conn = db_instance.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM transactions
        WHERE DATE(created_at) >= DATE(?) AND DATE(created_at) <= DATE(?)
        ORDER BY id ASC
    """, (date_from, date_to))
    trx_rows = cursor.fetchall()
    conn.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()

    elements = []
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1,
        spaceAfter=5
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=11,
        alignment=1,
        spaceAfter=15
    )

    elements.append(Paragraph("LAPORAN PENJUALAN - SISTEM KASIR POS", title_style))
    elements.append(Paragraph(f"Periode: {date_from} s/d {date_to}", subtitle_style))

    data = [
        ["No.", "No. Invoice", "Tanggal/Waktu", "Kasir", "Subtotal", "Diskon", "Total Omzet", "Metode"]
    ]

    total_omzet = 0
    for idx, r in enumerate(trx_rows, 1):
        data.append([
            str(idx),
            r["invoice_number"],
            r["created_at"][:16],
            r["cashier_name"],
            f"Rp{int(r['subtotal']):,}".replace(",", "."),
            f"Rp{int(r['discount']):,}".replace(",", "."),
            f"Rp{int(r['total']):,}".replace(",", "."),
            r["payment_method"].upper()
        ])
        total_omzet += r["total"]

    data.append([
        "TOTAL", "", "", "", "", "", f"Rp{int(total_omzet):,}".replace(",", "."), ""
    ])

    t = Table(data, colWidths=[30, 140, 110, 100, 90, 80, 110, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F1F5F9')),
    ]))

    elements.append(t)
    doc.build(elements)
    buffer.seek(0)

    filename = f"Laporan_Penjualan_{date_from}_sd_{date_to}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
