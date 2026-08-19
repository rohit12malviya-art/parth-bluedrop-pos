"""
PARTH BLUEDROP - High-Tech Web POS & ERP System
Specialized for Chocolate & Cold Drink Wholesale
Features:
- Instant Browser Print Window Trigger (Thermal & A4)
- Live WhatsApp Web API Integration
- Split-Panel POS Grid with Real-Time Calculations
- Dynamic UPI QR Code
"""

import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import urllib.parse
from datetime import datetime
import os
import streamlit.components.v1 as components

# --- Page Setup ---
st.set_page_config(
    page_title="PARTH BLUEDROP - Wholesale Web POS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom High-Tech Styling ---
st.markdown("""
<style>
    .main { background-color: #0b0f19; color: #f8fafc; }
    .stMetric { background-color: #1e293b; padding: 12px; border-radius: 8px; border-left: 4px solid #0284c7; }
    .pos-card {
        background: #1e293b;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #334155;
        margin-bottom: 12px;
    }
    .badge-profit {
        background: #059669;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

DB_NAME = "parth_bluedrop.db"
DEFAULT_UPI_ID = "9752162992@ybl"
BIZ_NAME = "PARTH BLUEDROP"
BIZ_TAGLINE = "Wholesale Distributor - Chocolates & Cold Drinks"
BIZ_PHONE = "9752162992"
BIZ_ADDRESS = "Purana Thana Road, Near SBI Bank, Gandhwani (M.P.) 454446"

def hash_txt(val):
    return hashlib.sha256(val.encode()).hexdigest()

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_db()
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
    c.execute("SELECT * FROM users WHERE role='Admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password_hash, role, recovery_pin_hash) VALUES (?, ?, ?, ?)",
                  ("admin", hash_txt("admin123"), "Admin", hash_txt("1234")))
    
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
    
    conn.commit()
    conn.close()

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

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        st.markdown(f"""
        <div style='text-align: center; background: #1e293b; padding: 25px; border-radius: 12px; border: 1px solid #0284c7;'>
            <h2 style='color: #38bdf8; margin: 0;'>⚡ {BIZ_NAME}</h2>
            <p style='color: #94a3b8; font-size: 13px;'>Wholesale ERP & Multi-Terminal POS</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("#### 🔐 Security Sign In")
            u = st.text_input("Operator / Admin Username")
            p = st.text_input("Password", type="password")
            btn_login = st.form_submit_button("🚀 ACCESS POS TERMINAL", use_container_width=True)
            
            if btn_login:
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT username, role FROM users WHERE username=? AND password_hash=?", (u.strip(), hash_txt(p.strip())))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state.authenticated = True
                    st.session_state.username = user[0]
                    st.session_state.role = user[1]
                    st.rerun()
                else:
                    st.error("Invalid Username or Password!")
        st.caption("Default Admin: **admin** | Pass: **admin123**")
    st.stop()


# --- SIDEBAR DASHBOARD ---
st.sidebar.markdown(f"""
<div style='background: #1e293b; padding: 12px; border-radius: 8px; border-left: 4px solid #38bdf8; margin-bottom: 15px;'>
    <h3 style='color: #38bdf8; margin: 0;'>⚡ {BIZ_NAME}</h3>
    <p style='color: #94a3b8; font-size: 11px; margin: 0;'>{BIZ_TAGLINE}</p>
    <div style='margin-top: 8px; font-size: 12px;'>👤 <b>{st.session_state.username}</b> <span style='color: #38bdf8;'>({st.session_state.role})</span></div>
</div>
""", unsafe_allow_html=True)

menu_options = ["🛒 High-Tech POS Billing", "👥 Customer Ledger & Udhaar"]
if st.session_state.role == "Admin":
    menu_options.extend(["📦 Inventory & Stock Control", "📊 Sales & Net Profit Dashboard"])

choice = st.sidebar.radio("Quick Navigation", menu_options)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout Session", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()


# ==============================================================================
# VIEW 1: HIGH-TECH SPLIT-GRID POS BILLING
# ==============================================================================
if choice == "🛒 High-Tech POS Billing":
    st.markdown("### 🛒 Terminal POS Billing")
    
    col_left, col_right = st.columns([1.5, 1.5], gap="medium")
    
    with col_left:
        # 1. Customer Card
        with st.container():
            st.markdown("<div class='pos-card'>", unsafe_allow_html=True)
            st.markdown("##### 👤 Customer Lookup")
            c_m1, c_m2, c_m3 = st.columns([1.5, 1.5, 1.5])
            
            mob = c_m1.text_input("Mobile No", max_chars=10, placeholder="10 Digit Mobile")
            c_name = "Cash Customer"
            c_village = ""
            old_udhaar = 0.0
            
            if len(mob) == 10:
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT name, village, outstanding_balance FROM customers WHERE mobile=?", (mob,))
                row = c.fetchone()
                conn.close()
                if row:
                    c_name, c_village, old_udhaar = row[0], row[1] or "", max(0.0, float(row[2]))
                    c_m2.text_input("Name", value=c_name, disabled=True)
                    c_m3.text_input("Village", value=c_village, disabled=True)
                else:
                    c_name = c_m2.text_input("Name", value="", placeholder="Enter Name")
                    c_village = c_m3.text_input("Village", value="", placeholder="Enter Village")
            else:
                c_m2.text_input("Name", value=c_name, disabled=True)
                c_m3.text_input("Village", value="-", disabled=True)
                
            st.markdown("</div>", unsafe_allow_html=True)

        # 2. Product Picker Card
        with st.container():
            st.markdown("<div class='pos-card'>", unsafe_allow_html=True)
            st.markdown("##### 📦 Add Product")
            
            conn = get_db()
            df_prods = pd.read_sql("SELECT id, barcode, name, buy_price, sell_price, stock FROM products ORDER BY name", conn)
            conn.close()
            
            p_c1, p_c2, p_c3 = st.columns([2, 1, 1])
            
            prod_map = {f"{r['name']} (₹{r['sell_price']} | Stock: {r['stock']})": r['id'] for _, r in df_prods.iterrows()}
            sel_label = p_c1.selectbox("Select Item", ["-- Select Item --"] + list(prod_map.keys()))
            qty = p_c2.number_input("Qty", min_value=1, value=1, step=1)
            
            p_c3.markdown("<br>", unsafe_allow_html=True)
            if p_c3.button("➕ Add Item", use_container_width=True, type="primary"):
                if sel_label != "-- Select Item --":
                    pid = prod_map[sel_label]
                    p_info = df_prods[df_prods['id'] == pid].iloc[0]
                    
                    if p_info['stock'] <= 0:
                        st.error("❌ Out of Stock!")
                    else:
                        in_cart = sum(item['qty'] for item in st.session_state.cart if item['id'] == pid)
                        if in_cart + qty > p_info['stock']:
                            st.error(f"Cannot add! Total available: {p_info['stock']}")
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

        # 3. Cart Table
        if st.session_state.cart:
            df_c = pd.DataFrame(st.session_state.cart)
            st.dataframe(df_c[['name', 'qty', 'sell', 'total']], use_container_width=True, hide_index=True)
            if st.button("🗑️ Reset Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()

    with col_right:
        # Payment Card
        st.markdown("<div class='pos-card'>", unsafe_allow_html=True)
        st.markdown("##### 💰 Payment Calculation")
        
        subtotal = sum(it['total'] for it in st.session_state.cart)
        total_profit = sum(it['profit'] for it in st.session_state.cart)
        net_payable = subtotal + old_udhaar
        
        m_col1, m_col2 = st.columns(2)
        m_col1.metric("Current Bill", f"₹ {subtotal:.2f}")
        m_col2.metric("Purana Udhaar", f"₹ {old_udhaar:.2f}", delta=f"-₹ {old_udhaar:.2f}" if old_udhaar > 0 else None, delta_color="inverse")
        
        st.markdown(f"<h3 style='color: #38bdf8; margin: 5px 0;'>Total Due: ₹ {net_payable:.2f}</h3>", unsafe_allow_html=True)
        
        if st.session_state.role == "Admin" and subtotal > 0:
            margin_pct = (total_profit / subtotal * 100) if subtotal > 0 else 0
            st.markdown(f"<span class='badge-profit'>📈 Net Margin: ₹ {total_profit:.2f} ({margin_pct:.1f}%)</span>", unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        paid = st.number_input("Received Cash / UPI (₹)", min_value=0.0, value=float(subtotal), step=50.0)
        remaining_balance = max(0.0, net_payable - paid)
        
        if remaining_balance > 0:
            st.markdown(f"<p style='color: #f87171; font-weight: bold;'>🚨 New Udhaar: ₹ {remaining_balance:.2f}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #4ade80; font-weight: bold;'>✅ Full Payment Cleared</p>", unsafe_allow_html=True)
            
        if st.button("🚀 SAVE & GENERATE INVOICE", type="primary", use_container_width=True):
            if not st.session_state.cart:
                st.error("Cart is empty!")
            elif not mob or len(mob) != 10:
                st.error("Please enter a valid 10-digit customer mobile number!")
            else:
                now = datetime.now()
                d_str, dt_str = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d %I:%M %p")
                conn = get_db()
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
                conn.close()
                
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
        
        # 4. DIRECT PRINT & RECEIPT PREVIEW (IF SAVED)
        if st.session_state.last_inv:
            inv = st.session_state.last_inv
            upi_amt = inv['paid'] if inv['paid'] > 0 else (inv['subtotal'] + inv['old_udhaar'])
            qr_src = f"https://api.qrserver.com/v1/create-qr-code/?size=130x130&data=upi://pay?pa={DEFAULT_UPI_ID}%26pn={urllib.parse.quote(BIZ_NAME)}%26am={upi_amt:.2f}%26cu=INR"
            
            items_html = "".join([f"<tr><td style='padding:4px; border-bottom:1px dashed #ccc;'>{it['name']}</td><td style='text-align:center; padding:4px; border-bottom:1px dashed #ccc;'>{it['qty']}</td><td style='text-align:right; padding:4px; border-bottom:1px dashed #ccc;'>₹{it['sell']:.2f}</td><td style='text-align:right; padding:4px; border-bottom:1px dashed #ccc; font-weight:bold;'>₹{it['total']:.2f}</td></tr>" for it in inv['items']])
            
            receipt_full_html = f"""
            <div id='printArea' style='background:#ffffff; color:#0f172a; padding:15px; border:1px solid #ddd; font-family:Arial,sans-serif; max-width:380px; margin:auto; border-radius:6px;'>
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
            
            # Interactive Printable Component
            components.html(f"""
            {receipt_full_html}
            <div style='text-align:center; margin-top:10px;'>
                <button onclick="window.print()" style="background:#0284c7; color:white; border:none; padding:10px 20px; font-size:13px; font-weight:bold; border-radius:6px; cursor:pointer; width:100%; max-width:380px;">
                    🖨️ DIRECT PRINT INVOICE
                </button>
            </div>
            """, height=560, scrolling=True)
            
            # WhatsApp Trigger Link
            items_str = "%0A".join([f"• {it['name']} x {it['qty']} = Rs.{it['total']:.2f}" for it in inv['items']])
            msg = f"*⚡ {BIZ_NAME} - INVOICE #{inv['inv_no']}*%0ANamaste *{inv['name']}* ji,%0A{items_str}%0A*Total: Rs.{inv['subtotal']:.2f}*%0APaid: Rs.{inv['paid']:.2f}%0AUdhaar: Rs.{inv['balance']:.2f}"
            wa_url = f"https://api.whatsapp.com/send?phone=91{inv['mob']}&text={msg}"
            st.markdown(f"<a href='{wa_url}' target='_blank'><button style='background-color:#22c55e; color:white; width:100%; border:none; padding:10px; border-radius:6px; font-weight:bold; cursor:pointer;'>💬 Open Direct WhatsApp Chat</button></a>", unsafe_allow_html=True)


# ==============================================================================
# VIEW 2: CUSTOMERS & UDHAAR
# ==============================================================================
elif choice == "👥 Customer Ledger & Udhaar":
    st.markdown("### 👥 Customer Ledger & Udhaar Tracking")
    conn = get_db()
    df_cust = pd.read_sql("SELECT id, mobile, name, village, outstanding_balance, last_purchase_date, last_purchase_amount FROM customers ORDER BY outstanding_balance DESC", conn)
    conn.close()
    
    st.dataframe(df_cust, use_container_width=True, hide_index=True)
    
    st.markdown("#### 💵 Receive Udhaar Payment")
    with st.form("rec_pay"):
        c1, c2 = st.columns(2)
        r_mob = c1.selectbox("Select Customer", df_cust['mobile'].tolist())
        r_amt = c2.number_input("Amount (₹)", min_value=1.0, step=50.0)
        if st.form_submit_button("Record Payment", use_container_width=True):
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE customers SET outstanding_balance = MAX(0.0, outstanding_balance - ?) WHERE mobile=?", (r_amt, r_mob))
            conn.commit()
            conn.close()
            st.success(f"₹ {r_amt:.2f} recorded!")
            st.rerun()


# ==============================================================================
# VIEW 3: INVENTORY CONTROL (ADMIN ONLY)
# ==============================================================================
elif choice == "📦 Inventory & Stock Control":
    st.markdown("### 📦 Inventory & Stock Control")
    conn = get_db()
    df_prods = pd.read_sql("SELECT id, barcode, name, category, buy_price, sell_price, stock FROM products ORDER BY id DESC", conn)
    conn.close()
    
    st.dataframe(df_prods, use_container_width=True, hide_index=True)
    
    with st.expander("➕ Add New Wholesale Product"):
        with st.form("add_p"):
            c1, c2 = st.columns(2)
            bcode = c1.text_input("Barcode")
            pname = c1.text_input("Product Name")
            pcat = c1.selectbox("Category", ["Chocolate Wholesale", "Cold Drink Wholesale", "Beverages", "Snacks"])
            bprice = c2.number_input("Buy Price ₹", min_value=0.0, step=5.0)
            sprice = c2.number_input("Sell Price ₹", min_value=0.0, step=5.0)
            pstock = c2.number_input("Stock Qty", min_value=0, step=10)
            
            if st.form_submit_button("Save to Inventory"):
                if pname:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT INTO products (barcode, name, category, buy_price, sell_price, stock) VALUES (?, ?, ?, ?, ?, ?)",
                              (bcode, pname, pcat, bprice, sprice, pstock))
                    conn.commit()
                    conn.close()
                    st.success(f"Added {pname}!")
                    st.rerun()


# ==============================================================================
# VIEW 4: PROFIT & ANALYTICS DASHBOARD (ADMIN ONLY)
# ==============================================================================
elif choice == "📊 Sales & Net Profit Dashboard":
    st.markdown("### 📊 Business Analytics & Profitability")
    
    f_date = st.date_input("Select Analysis Date", value=datetime.now())
    d_str = f_date.strftime("%Y-%m-%d")
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT SUM(total_amount), SUM(total_profit) FROM invoices WHERE date=?", (d_str,))
    res = c.fetchone()
    sales, profit = res[0] or 0.0, res[1] or 0.0
    
    c.execute("SELECT SUM(outstanding_balance) FROM customers WHERE outstanding_balance > 0")
    mkt_udh = c.fetchone()[0] or 0.0
    conn.close()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Selected Date Sales", f"₹ {sales:,.2f}")
    col2.metric("Date Net Profit (मुनाफा)", f"₹ {profit:,.2f}")
    col3.metric("Total Market Udhaar", f"₹ {mkt_udh:,.2f}")
    
    conn = get_db()
    df_inv = pd.read_sql(f"SELECT invoice_no, date_time, customer_name, customer_mobile, total_amount, paid_amount, udhaar_amount, total_profit, billed_by FROM invoices WHERE date='{d_str}' ORDER BY invoice_no DESC", conn)
    conn.close()
    
    st.markdown(f"#### Invoices on {d_str}")
    st.dataframe(df_inv, use_container_width=True, hide_index=True)
