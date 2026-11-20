/**
 * SISTEM KASIR MODERN (POS) - FRONTEND APP SCRIPT
 * Mengelola interaksi UI, Cart AJAX, Kalkulasi Kembalian, dan Cetak Struk
 */

document.addEventListener("DOMContentLoaded", function () {
    // 1. Live Clock di Header
    initLiveClock();

    // 2. Inisialisasi Fitur POS jika berada di halaman kasir
    if (document.getElementById("pos-product-container")) {
        initPosEngine();
    }
});

/**
 * Memperbarui waktu dan tanggal secara real-time di header
 */
function initLiveClock() {
    const clockEl = document.getElementById("header-live-clock");
    if (!clockEl) return;

    function update() {
        const now = new Date();
        const options = {
            weekday: 'long',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };
        clockEl.textContent = now.toLocaleDateString('id-ID', options);
    }
    update();
    setInterval(update, 1000);
}

/**
 * Format angka ke format mata uang Rupiah
 */
function formatRupiah(amount) {
    const num = Math.round(Number(amount) || 0);
    return 'Rp' + num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

/**
 * Mesin Utama POS (Point of Sale Engine)
 */
function initPosEngine() {
    const searchInput = document.getElementById("pos-search-input");
    const categoryPills = document.querySelectorAll(".category-pill");
    const cartContainer = document.getElementById("pos-cart-items");
    const cartSubtotalEl = document.getElementById("cart-subtotal");
    const cartDiscountEl = document.getElementById("cart-discount");
    const cartTotalEl = document.getElementById("cart-total");
    const discountTypeSelect = document.getElementById("discount-type");
    const discountInput = document.getElementById("discount-input");
    const cashInput = document.getElementById("cash-paid-input");
    const changeEl = document.getElementById("change-amount");
    const btnCheckout = document.getElementById("btn-checkout");
    const btnClearCart = document.getElementById("btn-clear-cart");

    let currentCartData = { items: [], subtotal: 0, total_items: 0 };
    let activeCategoryId = "";

    // 1. Load Keranjang Pertama Kali
    fetchCart();

    // 2. Filter Kategori
    categoryPills.forEach(pill => {
        pill.addEventListener("click", function () {
            categoryPills.forEach(p => p.classList.remove("active", "btn-primary"));
            categoryPills.forEach(p => p.classList.add("btn-outline-secondary"));
            this.classList.add("active", "btn-primary");
            this.classList.remove("btn-outline-secondary");

            activeCategoryId = this.getAttribute("data-category-id") || "";
            filterProductCards();
        });
    });

    // 3. Search Bar Produk & Barcode Scanner Listener
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            filterProductCards();
        });

        // Dukungan Barcode Scanner: Scanner biasanya menekan Enter setelah scan
        searchInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                const code = this.value.trim();
                if (code) {
                    addToCartByCode(code);
                    this.value = "";
                }
            }
        });
    }

    function filterProductCards() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : "";
        const cards = document.querySelectorAll(".pos-product-item");

        cards.forEach(card => {
            const name = (card.getAttribute("data-name") || "").toLowerCase();
            const code = (card.getAttribute("data-code") || "").toLowerCase();
            const catId = card.getAttribute("data-category-id") || "";

            const matchQuery = !query || name.includes(query) || code.includes(query);
            const matchCategory = !activeCategoryId || catId === activeCategoryId;

            if (matchQuery && matchCategory) {
                card.style.display = "block";
            } else {
                card.style.display = "none";
            }
        });
    }

    // 4. Klik Kartu Produk untuk Menambah ke Keranjang
    document.querySelectorAll(".pos-product-card").forEach(card => {
        card.addEventListener("click", function () {
            if (this.classList.contains("out-of-stock")) return;
            const productId = this.getAttribute("data-id");
            addToCart(productId, 1);
        });
    });

    // 5. API Fetch & Render Keranjang
    function fetchCart() {
        fetch("/api/pos/cart")
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    currentCartData = data.cart;
                    renderCart();
                }
            })
            .catch(err => console.error("Error fetching cart:", err));
    }

    function addToCart(productId, qty) {
        fetch("/api/pos/cart/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product_id: productId, quantity: qty })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    currentCartData = data.cart;
                    renderCart();
                } else {
                    alert(data.message || "Gagal menambahkan produk.");
                }
            });
    }

    function addToCartByCode(code) {
        fetch("/api/pos/cart/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: code, quantity: 1 })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    currentCartData = data.cart;
                    renderCart();
                } else {
                    alert(data.message || "Produk tidak ditemukan.");
                }
            });
    }

    window.updateCartQty = function (productId, qty) {
        fetch("/api/pos/cart/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product_id: productId, quantity: qty })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    currentCartData = data.cart;
                    renderCart();
                } else {
                    alert(data.message);
                }
            });
    };

    window.removeCartItem = function (productId) {
        fetch("/api/pos/cart/remove", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product_id: productId })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    currentCartData = data.cart;
                    renderCart();
                }
            });
    };

    if (btnClearCart) {
        btnClearCart.addEventListener("click", function () {
            if (currentCartData.items.length === 0) return;
            if (confirm("Kosongkan keranjang belanja?")) {
                fetch("/api/pos/cart/clear", { method: "POST" })
                    .then(res => res.json())
                    .then(data => {
                        currentCartData = data.cart;
                        renderCart();
                    });
            }
        });
    }

    function renderCart() {
        if (!cartContainer) return;

        if (currentCartData.items.length === 0) {
            cartContainer.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fa-solid fa-cart-shopping fa-3x mb-3 text-secondary opacity-50"></i>
                    <p class="mb-0">Keranjang masih kosong</p>
                    <small>Klik produk atau scan barcode untuk menambah</small>
                </div>
            `;
            if (btnCheckout) btnCheckout.disabled = true;
        } else {
            let html = "";
            currentCartData.items.forEach(item => {
                html += `
                    <div class="cart-item border-bottom py-2 d-flex align-items-center justify-content-between">
                        <div class="flex-grow-1 pe-2">
                            <h6 class="mb-0 fs-6 text-truncate" style="max-width: 170px;">${item.name}</h6>
                            <small class="text-muted">${formatRupiah(item.price)}</small>
                        </div>
                        <div class="d-flex align-items-center me-2">
                            <button class="btn btn-sm btn-outline-secondary px-2 py-0" onclick="updateCartQty(${item.product_id}, ${item.quantity - 1})">-</button>
                            <span class="mx-2 fw-bold">${item.quantity}</span>
                            <button class="btn btn-sm btn-outline-secondary px-2 py-0" onclick="updateCartQty(${item.product_id}, ${item.quantity + 1})">+</button>
                        </div>
                        <div class="text-end" style="min-width: 75px;">
                            <div class="fw-bold">${formatRupiah(item.subtotal)}</div>
                            <button class="btn btn-link text-danger p-0 fs-7" onclick="removeCartItem(${item.product_id})">
                                <i class="fa-solid fa-trash-can"></i>
                            </button>
                        </div>
                    </div>
                `;
            });
            cartContainer.innerHTML = html;
            if (btnCheckout) btnCheckout.disabled = false;
        }

        recalculateTotals();
    }

    // 6. Kalkulasi Ulang Subtotal, Diskon, Total, dan Kembalian
    function recalculateTotals() {
        const subtotal = currentCartData.subtotal || 0;
        const discountType = discountTypeSelect ? discountTypeSelect.value : "nominal";
        const discountVal = discountInput ? (parseFloat(discountInput.value) || 0) : 0;

        let discountAmount = 0;
        if (discountType === "percent") {
            discountAmount = (Math.min(discountVal, 100) / 100) * subtotal;
        } else {
            discountAmount = Math.min(discountVal, subtotal);
        }

        const grandTotal = Math.max(0, subtotal - discountAmount);

        if (cartSubtotalEl) cartSubtotalEl.textContent = formatRupiah(subtotal);
        if (cartDiscountEl) cartDiscountEl.textContent = formatRupiah(discountAmount);
        if (cartTotalEl) cartTotalEl.textContent = formatRupiah(grandTotal);

        // Hitung Kembalian
        const cashPaid = cashInput ? (parseFloat(cashInput.value.replace(/\D/g, "")) || 0) : 0;
        const change = cashPaid - grandTotal;

        if (changeEl) {
            changeEl.textContent = formatRupiah(Math.max(0, change));
            if (cashPaid > 0 && cashPaid < grandTotal) {
                changeEl.classList.add("text-danger");
                changeEl.textContent = "Kurang " + formatRupiah(grandTotal - cashPaid);
            } else {
                changeEl.classList.remove("text-danger");
            }
        }

        return { subtotal, discountAmount, grandTotal, cashPaid, change };
    }

    // Event listener untuk diskon dan uang bayar
    if (discountTypeSelect) discountTypeSelect.addEventListener("change", recalculateTotals);
    if (discountInput) discountInput.addEventListener("input", recalculateTotals);
    if (cashInput) cashInput.addEventListener("input", recalculateTotals);

    // Tombol Uang Cepat (Quick Cash Buttons)
    document.querySelectorAll(".btn-quick-cash").forEach(btn => {
        btn.addEventListener("click", function () {
            const addVal = parseInt(this.getAttribute("data-val") || "0");
            const totals = recalculateTotals();

            if (addVal === 0) {
                // Uang Pas
                if (cashInput) cashInput.value = totals.grandTotal;
            } else {
                const current = parseFloat(cashInput.value.replace(/\D/g, "")) || 0;
                if (cashInput) cashInput.value = current + addVal;
            }
            recalculateTotals();
        });
    });

    // 7. Proses Checkout Transaksi
    if (btnCheckout) {
        btnCheckout.addEventListener("click", function () {
            const totals = recalculateTotals();
            if (totals.cashPaid < totals.grandTotal) {
                alert(`Uang pembayaran kurang! Total tagihan adalah ${formatRupiah(totals.grandTotal)}.`);
                if (cashInput) cashInput.focus();
                return;
            }

            const paymentMethod = document.getElementById("payment-method") ? document.getElementById("payment-method").value : "cash";
            const notes = document.getElementById("transaction-notes") ? document.getElementById("transaction-notes").value : "";

            btnCheckout.disabled = true;
            btnCheckout.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Memproses...`;

            fetch("/api/pos/checkout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    discount_type: discountTypeSelect ? discountTypeSelect.value : "nominal",
                    discount_val: discountInput ? (parseFloat(discountInput.value) || 0) : 0,
                    cash_paid: totals.cashPaid,
                    payment_method: paymentMethod,
                    notes: notes
                })
            })
                .then(res => res.json())
                .then(data => {
                    btnCheckout.disabled = false;
                    btnCheckout.innerHTML = `<i class="fa-solid fa-check me-2"></i>Bayar & Cetak Struk`;

                    if (data.status === "success") {
                        // Reset input pembayaran
                        if (cashInput) cashInput.value = "";
                        if (discountInput) discountInput.value = "0";

                        // Kosongkan keranjang di frontend
                        currentCartData = { items: [], subtotal: 0, total_items: 0 };
                        renderCart();

                        // Tampilkan modal struk
                        showReceiptModal(data.transaction.id);
                    } else {
                        alert(data.message || "Gagal memproses transaksi.");
                    }
                })
                .catch(err => {
                    btnCheckout.disabled = false;
                    btnCheckout.innerHTML = `<i class="fa-solid fa-check me-2"></i>Bayar & Cetak Struk`;
                    alert("Terjadi kesalahan koneksi server.");
                });
        });
    }

    // 8. Tampilkan Modal Struk Transaksi
    window.showReceiptModal = function (transactionId) {
        const modalIframe = document.getElementById("receipt-iframe");
        const downloadPdfBtn = document.getElementById("btn-download-pdf");
        const receiptModalEl = document.getElementById("receiptModal");

        if (modalIframe) {
            modalIframe.src = `/pos/receipt/${transactionId}?paper=58`;
        }
        if (downloadPdfBtn) {
            downloadPdfBtn.href = `/transactions/${transactionId}/pdf`;
        }

        if (receiptModalEl && typeof bootstrap !== "undefined") {
            const modal = new bootstrap.Modal(receiptModalEl);
            modal.show();
        }
    };
}
