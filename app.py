"""
PARTH BLUEDROP - Next-Gen Fintech Wholesale ERP & Web POS
Bugfix: Crash-Proof Database Initialization & Thread-Safe SQLite
"""

import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import urllib.parse
from datetime import datetime
import os
import streamlit.components.v1 as components

# --- Page Config ---
st.set_page_config(
    page_title="PARTH BLUEDROP | Fintech Wholesale Cloud",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Digital Platform CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    .stApp {
        background: linear-gradient(135deg, #090d16 0%, #0f172a 50%, #020617 100%);
        color: #f1f5f9;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #0b1120 !important;
        border-right: 1px solid #1e293b;
    }
    
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetric"]:hover {
        border-color: #38bdf8;
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    
    .glass-card {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.4);
    }
    
    .glass-header {
        background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    .badge-profit {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: #ffffff;
        padding: 6px 14px;
        border-radius: 30px;
        font-weight: 700;
        font-size: 13px;
        display: inline-block;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
    }
    
    .badge-udhaar {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        color: #ffffff;
        padding: 6px 14px;
        border-radius: 30px;
        font-weight: 700;
        font-size: 13px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- Configuration & Database ---
DB_NAME = "parth_bluedrop.db"
DEFAULT_UPI_ID = "9752162992@ybl"
BIZ_NAME = "PARTH BLUEDROP"
BIZ_TAGLINE = "Wholesale Distributor - Chocolates & Cold Drinks"
BIZ_PHONE = "9752162992"
BIZ_ADDRESS = "Purana Thana Road, Near SBI Bank, Gandhwani, Dist - Dhar (M.P.) 454446"

def hash_txt(val):
    return hashlib.sha256(val.encode()).hexdigest()

def get_db():
    return sqlite3.connect(DB_NAME, timeout=20.0, check_same_thread=False)

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            recovery_pin_hash TEXT NOT NULL
        )
        """)
        
        # Thread-safe Admin sync without Table Locking
        c.execute("""
        INSERT INTO users (username, password_hash, role, recovery_pin_hash)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            password_hash=excluded.password_hash,
            role=excluded.role,
            recovery_pin_hash=excluded.recovery_pin_hash
        """, ("admin", hash_txt("admin123"), "Admin", hash_txt("1234")))
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mobile TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            village TEXT,
            outstanding_balance REAL DEFAULT 0.0,
            last_purchase_date TEXT,
            last_purchase_amount REAL DEFAULT 0.0
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            name TEXT NOT NULL,
            category TEXT,
            buy_price REAL NOT NULL,
            sell_price REAL NOT NULL,
            stock INTEGER NOT NULL,
            image_path TEXT,
            unit TEXT DEFAULT 'Box/Piece'
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_no INTEGER PRIMARY KEY AUTOINCREMENT,
            date_time TEXT NOT NULL,
            date TEXT NOT NULL,
            customer_mobile TEXT,
            customer_name TEXT,
            customer_village TEXT,
            subtotal REAL NOT NULL,
            discount REAL DEFAULT 0.0,
            total_amount REAL NOT NULL,
            paid_amount REAL NOT NULL,
            udhaar_amount REAL NOT NULL,
            total_profit REAL NOT NULL,
            payment_mode TEXT DEFAULT 'Cash',
            billed_by TEXT DEFAULT 'admin'
        )
        """)
        
        c.execute("PRAGMA table_info(invoices)")
        columns = [col[1] for col in c.fetchall()]
        if 'billed_by' not in columns:
            c.execute("ALTER TABLE invoices ADD COLUMN billed_by TEXT DEFAULT 'admin'")
            
        c.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no INTEGER,
            product_id INTEGER,
            product_name TEXT,
            qty INTEGER,
            buy_price REAL,
            sell_price REAL,
            total REAL,
            profit REAL
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS stock_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            product_name TEXT,
            qty_added INTEGER,
            buy_price REAL,
            total_cost REAL
        )
        """)
        conn.commit()

init_db()

# --- Session Authentication State ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'last_inv' not in st.session_state:
    st.session_state.last_inv = None

# --- AUTH / LOGIN SCREEN ---
if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown(f"""
        <div style='text-align: center; background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(20px); padding: 30px; border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.2); box-shadow: 0 20px 50px rgba(0,0,0,0.6);'>
            <h1 class='glass-header' style='font-size: 30px; margin: 0;'>⚡ {BIZ_NAME}</h1>
            <p style='color: #94a3b8; font-size: 13px; margin-top: 4px;'>Next-Gen Wholesale POS & Cloud Ledger</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("#### 🔐 Security Authentication")
            u = st.text_input("Username / Operator ID", value="admin")
            p = st.text_input("Password", type="password", value="admin123")
            btn_login = st.form_submit_button("🚀 ENTER PLATFORM TERMINAL", use_container_width=True)
            
            if btn_login:
                user_clean = u.strip().lower()
                pass_clean = p.strip()
                with get_db() as conn:
                    c = conn.cursor()
                    c.execute("SELECT username, role FROM users WHERE LOWER(username)=? AND password_hash=?", (user_clean, hash_txt(pass_clean)))
                    user = c.fetchone()
                if user:
                    st.session_state.authenticated = True
                    st.session_state.username = user[0]
                    st.session_state.role = user[1]
                    st.rerun()
                else:
                    st.error("Invalid Username or Password!")
        st.info("💡 Default: **admin** | Pass: **admin123**")
    st.stop()


# --- SIDEBAR BRANDING & MENU ---
st.sidebar.markdown(f"""
<div style='background: rgba(30, 41, 59, 0.5); backdrop-filter: blur(10px); padding: 16px; border-radius: 14px; border: 1px solid rgba(56, 189, 248, 0.2); margin-bottom: 20px;'>
    <div style='display: flex; align-items: center; gap: 8px;'>
        <h3 style='color: #38bdf8; margin: 0; font-size: 18px; font-weight: 800;'>⚡ {BIZ_NAME}</h3>
    </div>
    <p style='color: #94a3b8; font-size: 11px; margin: 4px 0 0 0;'>{BIZ_TAGLINE}</p>
    <div style='margin-top: 10px; padding-top: 8px; border-top: 1px solid #334155; font-size: 12px; color: #cbd5e1;'>
        👤 <b>{st.session_state.username}</b> <span style='background: #0284c7; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; margin-left: 4px;'>{st.session_state.role}</span>
    </div>
</div>
""", unsafe_allow_html=True)

menu_options = ["🛒 Digital POS Billing", "👥 Customer 360° & Udhaar Ledger"]
if st.session_state.role == "Admin":
    menu_options.extend(["📦 Inventory & Stock Control", "📊 Sales & Net Profit Dashboard"])

choice = st.sidebar.radio("Platform Modules", menu_options)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Terminate Session (Logout)", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.cart = []
    st.session_state.last_inv = None
    st.rerun()


# ==============================================================================
# MODULE 1: DIGITAL POS TERMINAL
# ==============================================================================
if choice == "🛒 Digital POS Billing":
    st.markdown("<h2 class='glass-header' style='margin-bottom: 15px;'>🛒 Next-Gen Web POS Terminal</h2>", unsafe_allow_html=True)
    
    col_pos_left, col_pos_right = st.columns([1.55, 1.45], gap="large")
    
    with col_pos_left:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #38bdf8; margin: 0 0 12px 0;'>👤 Customer Details & Lookup</h4>", unsafe_allow_html=True)
        
        c_col1, c_col2, c_col3 = st.columns([1.5, 1.5, 1.5])
        mob = c_col1.text_input("Mobile Number", max_chars=10, placeholder="10 Digit Number")
        c_name = "Cash Customer"
        c_village = ""
        old_udhaar = 0.0
        
        if len(mob) == 10:
            with get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT name, village, outstanding_balance, last_purchase_date, last_purchase_amount FROM customers WHERE mobile=?", (mob,))
                row = c.fetchone()
            if row:
                c_name, c_village, old_udhaar = row[0], row[1] or "", max(0.0, float(row[2]))
                c_col2.text_input("Customer Name", value=c_name, disabled=True)
                c_col3.text_input("Village / Area", value=c_village, disabled=True)
                
                if old_udhaar > 0:
                    st.markdown(f"<span class='badge-udhaar'>🚨 Past Udhaar Due: ₹ {old_udhaar:,.2f}</span> <span style='font-size:12px; color:#94a3b8; margin-left:8px;'>Last Bill: {row[3]} (₹{row[4]:,.2f})</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='background: #059669; color: white; padding: 4px 10px; border-radius: 20px; font-weight: bold; font-size: 12px;'>✅ No Past Udhaar</span>", unsafe_allow_html=True)
            else:
                c_name = c_col2.text_input("Customer Name", value="", placeholder="Enter Name")
                c_village = c_col3.text_input("Village / Area", value="", placeholder="Enter Village")
                st.caption("✨ New Customer Registration Mode")
        else:
            c_col2.text_input("Customer Name", value=c_name, disabled=True)
            c_col3.text_input("Village / Area", value="-", disabled=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #38bdf8; margin: 0 0 12px 0;'>📦 Add Wholesale Items</h4>", unsafe_allow_html=True)
        
        with get_db() as conn:
            df_prods = pd.read_sql("SELECT id, barcode, name, buy_price, sell_price, stock FROM products ORDER BY name", conn)
        
        p_c1, p_c2, p_c3 = st.columns([2.2, 1, 1])
        prod_map = {f"{r['name']} (₹{r['sell_price']} | Stock: {r['stock']})": r['id'] for _, r in df_prods.iterrows()}
        sel_label = p_c1.selectbox("Select Product", ["-- Select Item --"] + list(prod_map.keys()))
        qty = p_c2.number_input("Quantity", min_value=1, value=1, step=1)
        
        p_c3.markdown("<br>", unsafe_allow_html=True)
        if p_c3.button("➕ Add to Cart", use_container_width=True, type="primary"):
            if sel_label != "-- Select Item --":
                pid = prod_map[sel_label]
                p_info = df_prods[df_prods['id'] == pid].iloc[0]
                
                if p_info['stock'] <= 0:
                    st.error("❌ Out of Stock! Please update stock in Inventory.")
                else:
                    in_cart = sum(item['qty'] for item in st.session_state.cart if item['id'] == pid)
                    if in_cart + qty > p_info['stock']:
                        st.error(f"Cannot add! Max available: {p_info['stock']}")
                    else:
                        found = False
                        for item in st.session_state.cart:
                            if item['id'] == pid:
                                item['qty'] += qty
                                item['total'] = item['qty'] * item['sell']
                                item['profit'] = item['qty'] * (item['sell'] - item['buy'])
                                found = True
                                break
                        if not found:
                            st.session_state.cart.append({
                                'id': pid,
                                'name': p_info['name'],
                                'buy': p_info['buy_price'],
                                'sell': p_info['sell_price'],
                                'qty': qty,
                                'total': qty * p_info['sell_price'],
                                'profit': qty * (p_info['sell_price'] - p_info['buy_price'])
                            })
                        st.rerun()
                        
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.cart:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("##### 🛒 Current Cart Items")
            df_c = pd.DataFrame(st.session_state.cart)
            st.dataframe(
                df_c[['name', 'qty', 'sell', 'total']],
                column_config={
                    "name": "Product Name",
                    "qty": "Quantity",
                    "sell": "Rate (₹)",
                    "total": "Total (₹)"
                },
                use_container_width=True,
                hide_index=True
            )
            if st.button("🗑️ Clear Entire Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    with col_pos_right:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #38bdf8; margin: 0 0 12px 0;'>💰 Payment & Bill Breakdown</h4>", unsafe_allow_html=True)
        
        subtotal = sum(it['total'] for it in st.session_state.cart)
        total_profit = sum(it['profit'] for it in st.session_state.cart)
        net_payable = subtotal + old_udhaar
        
        m1, m2 = st.columns(2)
        m1.metric("Current Bill Total", f"₹ {subtotal:,.2f}")
        m2.metric("Old Udhaar (बकाया)", f"₹ {old_udhaar:,.2f}", delta=f"-₹ {old_udhaar:.2f}" if old_udhaar > 0 else None, delta_color="inverse")
        
        st.markdown(f"<h3 style='color: #38bdf8; margin: 12px 0;'>Net Payable Due: ₹ {net_payable:,.2f}</h3>", unsafe_allow_html=True)
        
        if st.session_state.role == "Admin" and subtotal > 0:
            margin_pct = (total_profit / subtotal * 100) if subtotal > 0 else 0
            st.markdown(f"<span class='badge-profit'>📈 Net Margin: ₹ {total_profit:.2f} ({margin_pct:.1f}%)</span>", unsafe_allow_html=True)
            
        st.markdown("<hr style='border-color: #334155; margin: 15px 0;'>", unsafe_allow_html=True)
        
        paid = st.number_input("Received Cash / UPI (जमा राशि ₹)", min_value=0.0, value=float(subtotal), step=50.0)
        remaining_balance = max(0.0, net_payable - paid)
        
        if remaining_balance > 0:
            st.markdown(f"<p style='color: #f87171; font-weight: bold; font-size: 15px;'>🚨 Remaining Udhaar: ₹ {remaining_balance:,.2f}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #4ade80; font-weight: bold; font-size: 15px;'>✅ Full Payment Received (No Udhaar)</p>", unsafe_allow_html=True)
            
        if st.button("🚀 SAVE & GENERATE INVOICE SLIP", type="primary", use_container_width=True):
            if not st.session_state.cart:
                st.error("Cart is empty! Please add products.")
            elif not mob or len(mob) != 10:
                st.error("Please enter a valid 10-digit customer mobile number!")
            else:
                now = datetime.now()
                d_str, dt_str = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d %I:%M %p")
                with get_db() as conn:
                    c = conn.cursor()
                    c.execute("""
                    INSERT INTO invoices (date_time, date, customer_mobile, customer_name, customer_village, subtotal, total_amount, paid_amount, udhaar_amount, total_profit, payment_mode, billed_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (dt_str, d_str, mob, c_name or "Customer", c_village, subtotal, subtotal, paid, remaining_balance, total_profit, "UPI/Cash", st.session_state.username))
                    inv_no = c.lastrowid
                    
                    for it in st.session_state.cart:
                        c.execute("""
                        INSERT INTO invoice_items (invoice_no, product_id, product_name, qty, buy_price, sell_price, total, profit)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (inv_no, it['id'], it['name'], it['qty'], it['buy'], it['sell'], it['total'], it['profit']))
                        c.execute("UPDATE products SET stock = stock - ? WHERE id=?", (it['qty'], it['id']))
                        
                    c.execute("""
                    INSERT INTO customers (mobile, name, village, outstanding_balance, last_purchase_date, last_purchase_amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(mobile) DO UPDATE SET
                        name=excluded.name,
                        village=excluded.village,
                        outstanding_balance=excluded.outstanding_balance,
                        last_purchase_date=excluded.last_purchase_date,
                        last_purchase_amount=excluded.last_purchase_amount
                    """, (mob, c_name or "Customer", c_village, remaining_balance, d_str, subtotal))
                    conn.commit()
                
                st.session_state.last_inv = {
                    'inv_no': inv_no,
                    'dt': dt_str,
                    'name': c_name,
                    'mob': mob,
                    'village': c_village,
                    'items': st.session_state.cart,
                    'subtotal': subtotal,
                    'old_udhaar': old_udhaar,
                    'paid': paid,
                    'balance': remaining_balance
                }
                st.session_state.cart = []
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.session_state.last_inv:
            inv = st.session_state.last_inv
            upi_amt = inv['paid'] if inv['paid'] > 0 else (inv['subtotal'] + inv['old_udhaar'])
            qr_src = f"https://api.qrserver.com/v1/create-qr-code/?size=130x130&data=upi://pay?pa={DEFAULT_UPI_ID}%26pn={urllib.parse.quote(BIZ_NAME)}%26am={upi_amt:.2f}%26cu=INR"
            
            items_html = "".join([f"<tr><td style='padding:4px; border-bottom:1px dashed #ccc;'>{it['name']}</td><td style='text-align:center; padding:4px; border-bottom:1px dashed #ccc;'>{it['qty']}</td><td style='text-align:right; padding:4px; border-bottom:1px dashed #ccc;'>₹{it['sell']:.2f}</td><td style='text-align:right; padding:4px; border-bottom:1px dashed #ccc; font-weight:bold;'>₹{it['total']:.2f}</td></tr>" for it in inv['items']])
            
            receipt_full_html = f"""
            <div id='printArea' style='background:#ffffff; color:#0f172a; padding:15px; border:1px solid #ddd; font-family:Arial,sans-serif; max-width:380px; margin:auto; border-radius:8px;'>
                <div style='text-align:center; border-bottom:2px dashed #0284c7; padding-bottom:8px;'>
                    <h3 style='margin:0; color:#0284c7;'>⚡ {BIZ_NAME}</h3>
                    <div style='font-size:11px;'>{BIZ_TAGLINE}</div>
                    <div style='font-size:10px; color:#64748b;'>{BIZ_ADDRESS}<br>Phone: {BIZ_PHONE}</div>
                </div>
                <div style='font-size:12px; margin:8px 0;'>
                    <b>Bill No:</b> #{inv['inv_no']} &nbsp;|&nbsp; <b>Date:</b> {inv['dt']}<br>
                    <b>Customer:</b> {inv['name']} ({inv['mob']})<br>
                    <b>Village:</b> {inv['village'] or 'N/A'}
                </div>
                <table style='width:100%; border-collapse:collapse; font-size:11px;'>
                    <thead><tr style='background:#0f172a; color:#ffffff;'><th>Item</th><th>Qty</th><th style='text-align:right;'>Rate</th><th style='text-align:right;'>Total</th></tr></thead>
                    <tbody>{items_html}</tbody>
                </table>
                <div style='margin-top:8px; font-size:12px; line-height:1.5; border-top:1px solid #ccc; padding-top:6px;'>
                    <div><b>Current Total:</b> ₹ {inv['subtotal']:.2f}</div>
                    <div>Purana Udhaar: ₹ {inv['old_udhaar']:.2f}</div>
                    <div style='color:#059669; font-weight:bold;'>Paid Amount: ₹ {inv['paid']:.2f}</div>
                    <div style='color:#dc2626; font-weight:bold;'>Remaining Udhaar: ₹ {inv['balance']:.2f}</div>
                </div>
                <div style='text-align:center; margin-top:10px; border-top:1px dashed #ccc; padding-top:6px;'>
                    <div style='font-size:10px; font-weight:bold; margin-bottom:4px;'>Scan & Pay via UPI</div>
                    <img src='{qr_src}' width='100' height='100'><br>
                    <small style='font-size:9px; color:#64748b;'>UPI: {DEFAULT_UPI_ID}</small>
                </div>
                <div style='text-align:center; font-size:10px; margin-top:8px; color:#64748b;'>*** Thank You! Visit Again ***</div>
            </div>
            """
            
            components.html(f"""
            {receipt_full_html}
            <div style='text-align:center; margin-top:10px;'>
                <button onclick="window.print()" style="background:#0284c7; color:white; border:none; padding:10px 20px; font-size:13px; font-weight:bold; border-radius:6px; cursor:pointer; width:100%; max-width:380px;">
                    🖨️ ONE-CLICK PRINT RECEIPT
                </button>
            </div>
            """, height=560, scrolling=True)
            
            items_str = "%0A".join([f"• {it['name']} x {it['qty']} = Rs.{it['total']:.2f}" for it in inv['items']])
            msg = f"*⚡ {BIZ_NAME} - INVOICE #{inv['inv_no']}*%0ANamaste *{inv['name']}* ji,%0A{items_str}%0A*Total: Rs.{inv['subtotal']:.2f}*%0APaid: Rs.{inv['paid']:.2f}%0AUdhaar: Rs.{inv['balance']:.2f}"
            wa_url = f"https://api.whatsapp.com/send?phone=91{inv['mob']}&text={msg}"
            st.markdown(f"<a href='{wa_url}' target='_blank'><button style='background-color:#22c55e; color:white; width:100%; border:none; padding:10px; border-radius:8px; font-weight:bold; cursor:pointer;'>💬 Open Direct WhatsApp Chat</button></a>", unsafe_allow_html=True)


# ==============================================================================
# MODULE 2: CUSTOMER 360° & MULTI-BILL LEDGER
# ==============================================================================
elif choice == "👥 Customer 360° & Udhaar Ledger":
    st.markdown("<h2 class='glass-header'>👥 Customer 360° & Udhaar Ledger</h2>", unsafe_allow_html=True)
    
    with get_db() as conn:
        df_cust = pd.read_sql("SELECT id, mobile, name, village, outstanding_balance, last_purchase_date, last_purchase_amount FROM customers ORDER BY outstanding_balance DESC", conn)
    
    col_l1, col_l2 = st.columns([1.6, 1.4], gap="large")
    
    with col_l1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("##### 📋 All Customers Directory")
        st.dataframe(
            df_cust,
            column_config={
                "mobile": "Mobile No",
                "name": "Customer Name",
                "village": "Village",
                "outstanding_balance": st.column_config.NumberColumn("Udhaar (₹)", format="₹ %.2f"),
                "last_purchase_date": "Last Date",
                "last_purchase_amount": st.column_config.NumberColumn("Last Bill (₹)", format="₹ %.2f")
            },
            use_container_width=True,
            hide_index=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("##### 💵 Quick Udhaar Collection Entry")
        with st.form("rec_pay_form"):
            r_c1, r_c2 = st.columns(2)
            sel_mob = r_c1.selectbox("Select Customer Mobile", df_cust['mobile'].tolist() if not df_cust.empty else ["No Customers"])
            r_amt = r_c2.number_input("Received Amount (₹)", min_value=1.0, step=50.0)
            
            if st.form_submit_button("Record Udhaar Deposit", use_container_width=True, type="primary"):
                if sel_mob != "No Customers":
                    with get_db() as conn:
                        c = conn.cursor()
                        c.execute("UPDATE customers SET outstanding_balance = MAX(0.0, outstanding_balance - ?) WHERE mobile=?", (r_amt, sel_mob))
                        conn.commit()
                    st.success(f"₹ {r_amt:,.2f} payment recorded for {sel_mob}!")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_l2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("##### 📜 Customer Multi-Bill History & Re-Print")
        
        target_cust = st.selectbox("Select Customer to View Full Ledger", options=df_cust['mobile'].tolist() if not df_cust.empty else [])
        
        if target_cust:
            with get_db() as conn:
                c_info = pd.read_sql(f"SELECT name, village, outstanding_balance FROM customers WHERE mobile='{target_cust}'", conn).iloc[0]
                df_invoices = pd.read_sql(f"SELECT invoice_no, date_time, total_amount, paid_amount, udhaar_amount, billed_by FROM invoices WHERE customer_mobile='{target_cust}' ORDER BY invoice_no DESC", conn)
            
            st.markdown(f"**Customer:** {c_info['name']} | **Village:** {c_info['village'] or 'N/A'}")
            st.markdown(f"<span class='badge-udhaar'>Total Due: ₹ {c_info['outstanding_balance']:,.2f}</span>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(
                df_invoices,
                column_config={
                    "invoice_no": "Inv #",
                    "date_time": "Date & Time",
                    "total_amount": st.column_config.NumberColumn("Total (₹)", format="₹ %.2f"),
                    "paid_amount": st.column_config.NumberColumn("Paid (₹)", format="₹ %.2f"),
                    "udhaar_amount": st.column_config.NumberColumn("Udhaar (₹)", format="₹ %.2f"),
                    "billed_by": "Operator"
                },
                use_container_width=True,
                hide_index=True
            )
            
            sel_inv_no = st.selectbox("Select Invoice to Re-Print / WhatsApp", options=df_invoices['invoice_no'].tolist() if not df_invoices.empty else [])
            if sel_inv_no:
                with get_db() as conn:
                    inv_data = pd.read_sql(f"SELECT * FROM invoices WHERE invoice_no={sel_inv_no}", conn).iloc[0]
                    inv_items = pd.read_sql(f"SELECT product_name, qty, sell_price, total FROM invoice_items WHERE invoice_no={sel_inv_no}", conn)
                
                items_str = "%0A".join([f"• {r['product_name']} x {r['qty']} = Rs.{r['total']:.2f}" for _, r in inv_items.iterrows()])
                msg = f"*⚡ {BIZ_NAME} - RE-PRINT INVOICE #{inv_data['invoice_no']}*%0ANamaste *{inv_data['customer_name']}* ji,%0A{items_str}%0A*Total: Rs.{inv_data['total_amount']:.2f}*%0APaid: Rs.{inv_data['paid_amount']:.2f}%0AUdhaar: Rs.{inv_data['udhaar_amount']:.2f}"
                wa_url = f"https://api.whatsapp.com/send?phone=91{inv_data['customer_mobile']}&text={msg}"
                st.markdown(f"<a href='{wa_url}' target='_blank'><button style='background-color:#22c55e; color:white; width:100%; border:none; padding:8px; border-radius:6px; font-weight:bold; cursor:pointer;'>💬 Re-Send Invoice on WhatsApp</button></a>", unsafe_allow_html=True)
                
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# MODULE 3: INVENTORY CONTROL & RESTOCK MANAGEMENT
# ==============================================================================
elif choice == "📦 Inventory & Stock Control":
    st.markdown("<h2 class='glass-header'>📦 Wholesale Inventory, Re-Stock & Price Control</h2>", unsafe_allow_html=True)
    
    with get_db() as conn:
        df_prods = pd.read_sql("SELECT id, barcode, name, category, buy_price, sell_price, stock FROM products ORDER BY id DESC", conn)
        df_stock_in = pd.read_sql("SELECT date, product_name, qty_added, buy_price, total_cost FROM stock_logs ORDER BY id DESC LIMIT 50", conn)
    
    t1, t2, t3 = st.tabs(["⚡ 1-Click Quick Restock & Edit", "📦 Full Product List", "🚛 Maal Aaya Logs (Inward Stock)"])
    
    with t1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("#### ⚡ Quick Stock Refill & Product Editor")
        st.caption("चुनें और नया स्टॉक जोड़ें (Stock Refill) या रेट बदलें")
        
        if not df_prods.empty:
            prod_dict = {f"#{r['id']} - {r['name']} (Current Stock: {r['stock']} | Buy: ₹{r['buy_price']} | Sell: ₹{r['sell_price']})": r['id'] for _, r in df_prods.iterrows()}
            selected_item_label = st.selectbox("Select Product to Update", list(prod_dict.keys()))
            selected_id = prod_dict[selected_item_label]
            
            p_data = df_prods[df_prods['id'] == selected_id].iloc[0]
            
            col_act1, col_act2 = st.columns(2, gap="large")
            
            with col_act1:
                st.markdown("##### ➕ Refill / Add New Units")
                with st.form("quick_refill_form"):
                    add_qty = st.number_input("Enter New Stock Incoming (Boxes/Pieces)", min_value=1, value=10, step=5)
                    b_rate = st.number_input("Purchase Rate for this Batch ₹", min_value=0.0, value=float(p_data['buy_price']), step=5.0)
                    
                    if st.form_submit_button("🚀 Add Stock & Record Log", type="primary", use_container_width=True):
                        with get_db() as conn:
                            c = conn.cursor()
                            c.execute("UPDATE products SET stock = stock + ?, buy_price = ? WHERE id = ?", (add_qty, b_rate, selected_id))
                            c.execute("INSERT INTO stock_logs (date, product_name, qty_added, buy_price, total_cost) VALUES (?, ?, ?, ?, ?)",
                                      (datetime.now().strftime("%Y-%m-%d"), p_data['name'], add_qty, b_rate, add_qty * b_rate))
                            conn.commit()
                        st.success(f"✅ {add_qty} units added to '{p_data['name']}'! Total stock is now {p_data['stock'] + add_qty}.")
                        st.rerun()

            with col_act2:
                st.markdown("##### ✏️ Edit Product Details & Prices")
                with st.form("edit_details_form"):
                    e_name = st.text_input("Product Name", value=p_data['name'])
                    e_bcode = st.text_input("Barcode", value=str(p_data['barcode'] or ""))
                    e_cat = st.selectbox("Category", ["Chocolate Wholesale", "Cold Drink Wholesale", "Juice & Beverages", "Snacks"], index=["Chocolate Wholesale", "Cold Drink Wholesale", "Juice & Beverages", "Snacks"].index(p_data['category']) if p_data['category'] in ["Chocolate Wholesale", "Cold Drink Wholesale", "Juice & Beverages", "Snacks"] else 0)
                    
                    e_col_a, e_col_b = st.columns(2)
                    e_buy = e_col_a.number_input("Buy Price ₹", min_value=0.0, value=float(p_data['buy_price']), step=5.0)
                    e_sell = e_col_b.number_input("Sell Price ₹", min_value=0.0, value=float(p_data['sell_price']), step=5.0)
                    e_exact_stock = st.number_input("Force Set Exact Stock", min_value=0, value=int(p_data['stock']), step=1)
                    
                    if st.form_submit_button("💾 Save Product Changes", use_container_width=True):
                        with get_db() as conn:
                            c = conn.cursor()
                            c.execute("UPDATE products SET name=?, barcode=?, category=?, buy_price=?, sell_price=?, stock=? WHERE id=?",
                                      (e_name, e_bcode, e_cat, e_buy, e_sell, e_exact_stock, selected_id))
                            conn.commit()
                        st.success(f"Product #{selected_id} updated successfully!")
                        st.rerun()
        else:
            st.info("No products found. Please add a product below.")
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        with st.expander("➕ Register Brand New Product"):
            with st.form("add_new_prod_form"):
                n_c1, n_c2 = st.columns(2)
                bcode = n_c1.text_input("Barcode / Item Code")
                pname = n_c1.text_input("Product Name")
                pcat = n_c1.selectbox("Category", ["Chocolate Wholesale", "Cold Drink Wholesale", "Juice & Beverages", "Snacks"])
                bprice = n_c2.number_input("Wholesale Buy Price ₹", min_value=0.0, step=5.0)
                sprice = n_c2.number_input("Retailer Sell Price ₹", min_value=0.0, step=5.0)
                pstock = n_c2.number_input("Initial Stock Units", min_value=0, step=10)
                
                if st.form_submit_button("Save New Product", use_container_width=True, type="primary"):
                    if pname:
                        with get_db() as conn:
                            c = conn.cursor()
                            c.execute("INSERT INTO products (barcode, name, category, buy_price, sell_price, stock) VALUES (?, ?, ?, ?, ?, ?)",
                                      (bcode, pname, pcat, bprice, sprice, pstock))
                            c.execute("INSERT INTO stock_logs (date, product_name, qty_added, buy_price, total_cost) VALUES (?, ?, ?, ?, ?)",
                                      (datetime.now().strftime("%Y-%m-%d"), pname, pstock, bprice, pstock * bprice))
                            conn.commit()
                        st.success(f"Added '{pname}' with {pstock} units!")
                        st.rerun()

    with t2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("##### 📦 Live Products & Stock Level Directory")
        st.dataframe(
            df_prods,
            column_config={
                "barcode": "Barcode",
                "name": "Product Name",
                "category": "Category",
                "buy_price": st.column_config.NumberColumn("Buy Rate (₹)", format="₹ %.2f"),
                "sell_price": st.column_config.NumberColumn("Sell Rate (₹)", format="₹ %.2f"),
                "stock": st.column_config.NumberColumn("Available Stock", format="%d units")
            },
            use_container_width=True,
            hide_index=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with t3:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("##### 🚛 Purchase & Maal Aaya Inward History")
        st.dataframe(
            df_stock_in,
            column_config={
                "date": "Date",
                "product_name": "Product Name",
                "qty_added": "Qty Added",
                "buy_price": st.column_config.NumberColumn("Buy Rate (₹)", format="₹ %.2f"),
                "total_cost": st.column_config.NumberColumn("Total Inward Cost (₹)", format="₹ %.2f")
            },
            use_container_width=True,
            hide_index=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# MODULE 4: NET PROFIT & ANALYTICS DASHBOARD
# ==============================================================================
elif choice == "📊 Sales & Net Profit Dashboard":
    st.markdown("<h2 class='glass-header'>📊 Financial Analytics & Net Profit Engine</h2>", unsafe_allow_html=True)
    
    f_date = st.date_input("Select Analysis Date", value=datetime.now())
    d_str = f_date.strftime("%Y-%m-%d")
    
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT SUM(total_amount), SUM(total_profit) FROM invoices WHERE date=?", (d_str,))
        res = c.fetchone()
        sales, profit = res[0] or 0.0, res[1] or 0.0
        
        c.execute("SELECT SUM(outstanding_balance) FROM customers WHERE outstanding_balance > 0")
        mkt_udh = c.fetchone()[0] or 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Daily Sales Volume", f"₹ {sales:,.2f}")
    col2.metric("Daily Net Profit (शुद्ध मुनाफा)", f"₹ {profit:,.2f}")
    col3.metric("Total Market Udhaar Outstanding", f"₹ {mkt_udh:,.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with get_db() as conn:
        df_inv = pd.read_sql(f"SELECT invoice_no, date_time, customer_name, customer_mobile, total_amount, paid_amount, udhaar_amount, total_profit, billed_by FROM invoices WHERE date='{d_str}' ORDER BY invoice_no DESC", conn)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown(f"#### Invoices Generated on {d_str}")
    st.dataframe(
        df_inv,
        column_config={
            "invoice_no": "Inv #",
            "date_time": "Time",
            "customer_name": "Customer",
            "customer_mobile": "Mobile",
            "total_amount": st.column_config.NumberColumn("Bill Total (₹)", format="₹ %.2f"),
            "paid_amount": st.column_config.NumberColumn("Paid (₹)", format="₹ %.2f"),
            "udhaar_amount": st.column_config.NumberColumn("Udhaar (₹)", format="₹ %.2f"),
            "total_profit": st.column_config.NumberColumn("Profit (₹)", format="₹ %.2f"),
            "billed_by": "Billed By"
        },
        use_container_width=True,
        hide_index=True
    )
    st.markdown("</div>", unsafe_allow_html=True)
