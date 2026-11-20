# 🛒 Modern Point of Sale (POS) & Retail Management System

Aplikasi Web **Sistem Kasir (Point of Sale / POS)** modern, profesional, responsif, dan siap produksi (*production-ready*) yang dibangun menggunakan **Python (Flask)**, **SQLite**, dan arsitektur murni **Object-Oriented Programming (OOP)**, didukung antarmuka pengguna berbasis **Bootstrap 5**, **Chart.js**, dan **Font Awesome**.

---

## 🌟 Fitur Utama Aplikasi

### 1. 📊 Dashboard Analitik Interaktif
- **Ringkasan Penjualan:** Penjualan hari ini, jumlah transaksi, total katalog produk, peringatan stok menipis ($\le 5$), dan total omzet.
- **Visualisasi Chart.js:** Grafik garis tren omzet 7 hari terakhir dan diagram donat penjualan kategori terlaris.
- **Tabel Peringkat:** Top 5 produk terlaris dengan total kuantitas dan omzet.
- **Histori Cepat:** 5 transaksi kasir terbaru secara *real-time*.

### 2. 💻 Kasir / Point of Sale (POS Screen)
- **Katalog Visual:** Kartu produk dengan informasi nama, kode barcode, harga jual, dan status stok.
- **Pencarian Cepat & Barcode Scanner:** Filter instan dengan teks maupun *barcode scanner hardware* (otomatis terinput saat tombol Enter ditekan).
- **Filter Kategori:** Tombol pill kategori untuk navigasi cepat.
- **Keranjang Belanja Real-Time:** Penambahan produk via AJAX, ubah kuantitas ($+/-$), hapus item, dan reset keranjang.
- **Sistem Diskon:** Fleksibel dengan potongan nominal (Rp) maupun persentase (%).
- **Kalkulasi Kembalian Otomatis:** Deteksi uang kurang dan hitung uang kembalian secara presisi.
- **Tombol Uang Cepat (Quick Cash):** Uang Pas, $+10\text{k}$, $+20\text{k}$, $+50\text{k}$, $+100\text{k}$.
- **Checkout Atomik (ACID):** Pengurangan stok dan pencatatan transaksi terjadi secara atomik di database (tidak ada data korup jika terjadi kegagalan).

### 3. 🧾 Cetak Struk Transaksi & PDF
- **Struk Thermal Printer:** Layout khusus printer thermal **58mm** dan **80mm** dengan CSS `@media print`.
- **Ekspor PDF Struk:** Unduh berkas PDF struk langsung dari browser menggunakan engine `reportlab`.

### 4. 📦 Manajemen Produk & Kategori (CRUD)
- Tambah, edit, dan hapus produk dengan validasi ketat (kode unik, harga/stok non-negatif).
- *Auto-generator* kode produk otomatis (`PRD-XXX`).
- Pengelompokan produk berdasarkan kategori.

### 5. 📈 Laporan Penjualan & Ekspor
- Filter periode: Hari ini, Minggu ini, Bulan ini, dan Rentang Tanggal Kustom.
- Ringkasan omzet, total transaksi, total diskon, dan estimasi laba kotor (Omzet dikurangi HPP/Modal).
- **Ekspor Excel (.xlsx):** Menggunakan `openpyxl` dengan format tabel rapi dan auto-styling.
- **Ekspor PDF Laporan (.pdf):** Menggunakan `reportlab` dalam orientasi landscape A4.

### 6. 🔐 Autentikasi & Otorisasi Pengguna (Role-Based Access)
- **Role Admin:** Mengakses seluruh fitur dashboard, produk, kategori, laporan, manajemen pengguna, dan pengaturan toko.
- **Role Kasir:** Akses fokus pada POS kasir dan riwayat transaksi.
- Password dienkripsi dengan *hashing salt* (`pbkdf2:sha256`) via Werkzeug Security.
- Proteksi route dengan decorator `@login_required` dan `@admin_required`.

---

## 🏗️ Struktur Proyek

```text
pos-system/
├── app.py                     # Entry point & factory Flask app
├── config.py                  # Konfigurasi aplikasi & database
├── requirements.txt           # Dependensi Python
├── Procfile                   # Konfigurasi deployment server production (Gunicorn)
├── .env.example               # Contoh environment variable
├── .gitignore                 # Filter berkas repository git
│
├── models/                    # Lapisan Arsitektur OOP
│   ├── __init__.py
│   ├── database.py            # Class Database (Koneksi & Transaksi Atomik)
│   ├── product.py             # Class Product (Encapsulation, Property/Setter)
│   ├── cart.py                # Class Cart (Keranjang Belanja)
│   ├── transaction.py         # Class Transaction (Static Method Diskon & Invoice)
│   ├── cashier.py             # Class Cashier (Alur Checkout Atomik)
│   ├── user.py                # Class User (Autentikasi & Enkripsi Password)
│   └── category.py            # Class Category (Pengelompokan Produk)
│
├── routes/                    # Modular Blueprints
│   ├── __init__.py
│   ├── auth.py                # Login, Logout, Decorator Role
│   ├── dashboard.py           # Statistik & Grafik Dashboard
│   ├── cashier.py             # Endpoint Layar Kasir & AJAX POS
│   ├── products.py            # CRUD Data Produk & Upload Gambar
│   ├── categories.py          # CRUD Kategori Produk
│   ├── transactions.py        # Riwayat Transaksi & Cetak Struk
│   ├── reports.py             # Laporan Penjualan & Ekspor Excel/PDF
│   ├── settings.py            # Pengaturan Identitas Toko & Ganti Password
│   └── users.py               # Manajemen Akun Staf & Hak Akses
│
├── templates/                 # Tampilan Frontend Jinja2 & Bootstrap 5
│   ├── base.html              # Layout Master (Sidebar, Header, Live Clock)
│   ├── login.html             # Halaman Login Modern
│   ├── dashboard.html         # Dashboard Admin & Chart.js
│   ├── cashier.html           # Antarmuka Layar Kasir POS
│   ├── products.html          # Halaman CRUD Produk
│   ├── categories.html        # Halaman Kategori Produk
│   ├── transactions.html      # Halaman Riwayat Transaksi
│   ├── reports.html           # Halaman Laporan & Ekspor
│   ├── settings.html          # Halaman Pengaturan Toko
│   ├── users.html             # Halaman Manajemen Akun
│   └── receipt_thermal.html   # Template Khusus Struk Printer Thermal
│
├── static/
│   ├── css/
│   │   └── style.css          # Desain Modern (Navy/Blue Theme, Scrollbar, Print CSS)
│   ├── js/
│   │   └── app.js             # Real-Time POS Engine, AJAX Cart, Live Clock
│   └── uploads/               # Direktori Simpanan Foto Produk
│
└── instance/
    └── pos.db                 # Database SQLite Persisten
```

---

## 🧩 Penerapan Konsep OOP Lengkap

Aplikasi ini memenuhi **seluruh 8 ketentuan OOP** yang diwajibkan:

### 1. Class
Dibuat class-class utama yang memisahkan tanggung jawab secara modular:
- `Product` (`models/product.py`): Mengelola entitas produk.
- `Cart` (`models/cart.py`): Mengelola keranjang belanja dan kuantitas.
- `Transaction` (`models/transaction.py`): Mengelola struk dan kalkulasi pembayaran.
- `Cashier` (`models/cashier.py`): Mengontrol alur operasional kasir secara atomik.
- `Database` (`models/database.py`): Mengelola koneksi dan migrasi tabel SQLite.
- `User` (`models/user.py`): Mengelola otentikasi akun dan peran pengguna.
- `Category` (`models/category.py`): Mengelola pengelompokan barang.

### 2. Object (Instance Creation)
Objek dibuat secara dinamis saat aplikasi berjalan, misalnya:
```python
# Membuat objek Kasir dan memproses checkout
cashier_obj = Cashier(user_id=session.get('user_id'), cashier_name=session.get('full_name'))
transaction_obj = cashier_obj.process_checkout(cart=user_cart, cash_paid=50000)
```

### 3. Constructor `__init__()`
Setiap class memiliki constructor untuk inisialisasi state awal:
```python
class Product:
    def __init__(self, id, code, name, category_id, cost_price, price, stock, image=None, description=None):
        self.id = id
        self.code = code.upper().strip()
        self.name = name.strip()
        self.__price = 0.0
        self.__stock = 0
        self.price = price   # Memanggil @price.setter
        self.stock = stock   # Memanggil @stock.setter
```

### 4. Attribute & Method
- **Attribute Publik:** `code`, `name`, `category_id`, `invoice_number`.
- **Attribute Private:** `__price`, `__stock`, `__cost_price`, `__password_hash`, `__items`.
- **Method Fungsional:** `decrease_stock()`, `add_item()`, `calculate_subtotal()`, `process_checkout()`.

### 5. Encapsulation (Atribut Private `__`)
Melindungi data sensitif dari perubahan langsung tanpa melalui validasi logika bisnis:
```python
class Cart:
    def __init__(self):
        # Data belanja diisolasi di atribut private __items
        self.__items = {}

    @property
    def items(self):
        return self.__items
```

### 6. Property & Setter (`@property` dan `@<nama>.setter`)
Mengatur akses baca/tulis terhadap atribut private dengan validasi ketat:
```python
@property
def price(self) -> float:
    return self.__price

@price.setter
def price(self, value: float):
    val = float(value)
    if val < 0:
        raise ValueError("Harga produk tidak boleh bernilai negatif.")
    self.__price = val

@property
def stock(self) -> int:
    return self.__stock

@stock.setter
def stock(self, value: int):
    val = int(value)
    if val < 0:
        raise ValueError("Jumlah stok tidak boleh negatif.")
    self.__stock = val
```

### 7. Class Method (`@classmethod`)
Membuat objek langsung dari row database (`Row Factory`) atau mengelola operasi level class:
```python
@classmethod
def from_db_row(cls, row):
    if row is None:
        return None
    return cls(
        id=row["id"],
        code=row["code"],
        name=row["name"],
        category_id=row["category_id"],
        cost_price=row["cost_price"],
        price=row["price"],
        stock=row["stock"]
    )
```

### 8. Static Method (`@staticmethod`)
Fungsi utilitas murni yang tidak terikat pada instance (`self`) maupun class (`cls`):
```python
@staticmethod
def calculate_discount(subtotal: float, discount_type: str = "nominal", discount_val: float = 0.0) -> float:
    if discount_type == "percent":
        return (min(float(discount_val), 100.0) / 100.0) * subtotal
    return min(float(discount_val), subtotal)

@staticmethod
def validate_payment(total: float, cash_paid: float) -> bool:
    return float(cash_paid) >= float(total)

@staticmethod
def generate_invoice_number() -> str:
    now = datetime.now()
    return f"INV-{now.strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"
```

---

## ⚡ Panduan Instalasi & Menjalankan Lokal

### 1. Prasyarat
- Python 3.9 atau lebih baru.
- Pip (Python Package Manager).

### 2. Buka Direktori Proyek
```bash
cd c:\Users\lenovo\Documents\kasir
```

### 3. Buat Virtual Environment (Disarankan)
```bash
# Windows
py -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependensi
```bash
pip install -r requirements.txt
```

### 5. Jalankan Aplikasi
```bash
# Menggunakan Python Launcher (Windows)
py app.py

# Atau menggunakan python standar
python app.py
```

Buka browser dan akses alamat:
```text
http://127.0.0.1:5000
```

---

## 🔑 Akun Demo Bawaan

Database SQLite otomatis diinisialisasi pada saat aplikasi pertama kali dijalankan dengan data akun berikut:

| Peran (Role) | Username | Password | Hak Akses |
|:---|:---|:---|:---|
| **Administrator** | `admin` | `admin123` | Akses penuh ke seluruh menu dan pengaturan |
| **Kasir** | `kasir1` | `kasir123` | Akses khusus menu Kasir POS & Riwayat Transaksi |

> [!TIP]
> Password dapat diubah sewaktu-waktu melalui menu **Pengaturan > Keamanan Akun** atau diubah melalui file `.env`.

---

## 🚀 Panduan Deployment ke Cloud (Siap Produksi)

Aplikasi ini sudah dilengkapi dengan `Procfile`, konfigurasi environment variable, dan database SQLite persisten.

### A. Deploy ke Platform Render.com
1. Buat repository baru di GitHub dan lakukan push source code proyek.
2. Buka dashboard [Render.com](https://render.com) dan buat **New Web Service**.
3. Hubungkan repository GitHub Anda.
4. Masukkan konfigurasi berikut:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Tambahkan **Disk Persisten** (Render Persistent Disk) jika ingin database SQLite tetap tersimpan saat redeploy:
   - Mount Path: `/opt/render/project/src/instance`
   - Size: 1 GB
6. Tambahkan Environment Variables:
   - `SECRET_KEY`: `<string_acak_rahasia>`
   - `FLASK_ENV`: `production`

### B. Deploy ke Railway.app
1. Di [Railway.app](https://railway.app), klik **New Project** -> **Deploy from GitHub repo**.
2. Railway akan otomatis mendeteksi file `Procfile` (`web: gunicorn app:app`) dan `requirements.txt`.
3. Tambahkan volume persisten di tab **Settings > Volumes** ke path `/app/instance`.
4. Aplikasi akan otomatis live dengan URL HTTPS gratis.

### C. Deploy ke VPS Linux (Ubuntu / Debian dengan Nginx + Gunicorn)
1. Install Python dan Nginx:
   ```bash
   sudo apt update && sudo apt install python3-pip python3-venv nginx -y
   ```
2. Clone proyek ke folder `/var/www/kasir`.
3. Buat service systemd untuk Gunicorn:
   ```ini
   [Unit]
   Description=Gunicorn POS Application
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/kasir
   ExecStart=/var/www/kasir/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app

   [Install]
   WantedBy=multi-user.target
   ```
4. Hubungkan Nginx sebagai reverse proxy ke `http://127.0.0.1:5000`.
