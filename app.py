"""
PARTH BLUEDROP - Next-Gen Fintech Wholesale ERP & Web POS
Updated Credentials & UPI ID:
- UPI: 9752162992@ybl
- User: parthkirana / Parth@1122 (PIN: 1122)
- Feature: Direct Manual Item Entry (Without Inventory Pre-Save)
"""

import streamlit as st
import pandas as pd
import hashlib
import urllib.parse
from datetime import datetime
import os
import streamlit.components.v1 as components
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# --- Page Config ---
st.set_page_config(
    page_title="PARTH BLUEDROP | Fintech Wholesale Cloud",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
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
    }
    .badge-profit {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: #ffffff;
        padding: 6px 14px;
        border-radius: 30px;
        font-weight: 700;
        font-size: 13px;
        display: inline-block;
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
    .btn-sms {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: bold;
        text-align: center;
        display: block;
        width: 100%;
        text-decoration: none;
        cursor: pointer;
    }
    .btn-wa {
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
        color: white;
        border: none;
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: bold;
        text-align: center;
        display: block;
        width: 100%;
        text-decoration: none;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

CLOUD_DB_URL = "postgresql+psycopg2://postgres.bawmdovylsaagnfufjiy:Rohit%4062992@aws-0-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require"
DEFAULT_UPI_ID = "9752162992@ybl"
BIZ_NAME = "PARTH BLUEDROP"
BIZ_TAGLINE = "Wholesale Distributor - Chocolates & Cold Drinks"
BIZ_PHONE = "9752162992"
BIZ_ADDRESS = "Purana Thana Road, Near SBI Bank, Gandhwani, Dist - Dhar (M.P.) 454446"

@st.cache_resource
def get_engine():
    try:
        eng = create_engine(CLOUD_DB_URL, poolclass=NullPool, connect_args={"connect_timeout": 8})
        with eng.connect() as test_conn:
            test_conn.execute(text("SELECT 1"))
        return eng, "Supabase Cloud 🟢"
    except Exception:
        local_eng = create_engine("sqlite:///parth_bluedrop.db", connect_args={"check_same_thread": False})
        return local_eng, "Local Mirror 🟡"

def hash_txt(val):
    return hashlib.sha256(val.encode()).hexdigest()

def init_db():
    engine, _ = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            recovery_pin_hash TEXT NOT NULL
        );
        """))
        try:
            conn.execute(text("""
            INSERT INTO users (username, password_hash, role, recovery_pin_hash)
            VALUES (:u, :p, :r, :pin)
            ON CONFLICT(username) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                recovery_pin_hash = EXCLUDED.recovery_pin_hash;
            """), {"u": "parthkirana", "p": hash_txt("Parth@1122"), "r": "Admin", "pin": hash_txt("1122")})
        except Exception:
            pass

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            mobile TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            village TEXT,
            outstanding_balance DOUBLE PRECISION DEFAULT 0.0,
            last_purchase_date TEXT,
            last_purchase_amount DOUBLE PRECISION DEFAULT 0.0
        );
        """))
        
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            barcode TEXT,
            name TEXT NOT NULL,
            category TEXT,
            buy_price DOUBLE PRECISION NOT NULL,
            sell_price DOUBLE PRECISION NOT NULL,
            stock INTEGER NOT NULL,
            image_path TEXT,
            unit TEXT DEFAULT 'Box/Piece'
        );
        """))
        
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_no SERIAL PRIMARY KEY,
            date_time TEXT NOT NULL,
            date TEXT NOT NULL,
            customer_mobile TEXT,
            customer_name TEXT,
            customer_village TEXT,
            subtotal DOUBLE PRECISION NOT NULL,
            discount DOUBLE PRECISION DEFAULT 0.0,
            total_amount DOUBLE PRECISION NOT NULL,
            paid_amount DOUBLE PRECISION NOT NULL,
            udhaar_amount DOUBLE PRECISION NOT NULL,
            total_profit DOUBLE PRECISION NOT NULL,
            payment_mode TEXT DEFAULT 'Cash',
            billed_by TEXT DEFAULT 'parthkirana'
        );
        """))
        
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id SERIAL PRIMARY KEY,
            invoice_no INTEGER,
            product_id INTEGER,
            product_name TEXT,
            qty INTEGER,
            buy_price DOUBLE PRECISION,
            sell_price DOUBLE PRECISION,
            total DOUBLE PRECISION,
            profit DOUBLE PRECISION
        );
        """))

try:
    init_db()
except Exception:
    pass

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'last_inv' not in st.session_state:
    st.session_state.last_inv = None
if 'last_udhaar_rec' not in st.session_state:
    st.session_state.last_udhaar_rec = None

# --- AUTH LOGIN ---
if not st.session_state.authenticated:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown(f"""
        <div style='text-align: center; background: rgba(15, 23, 42, 0.85); padding: 30px; border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.2);'>
            <h1 class='glass-header' style='font-size: 30px; margin: 0;'>⚡ {BIZ_NAME}</h1>
            <p style='color: #94a3b8; font-size: 13px; margin-top: 4px;'>Wholesale POS & ERP</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("#### 🔐 Security Authentication")
            u = st.text_input("Username / Operator ID", value="parthkirana")
            p = st.text_input("Password", type="password", value="Parth@1122")
            if st.form_submit_button("🚀 ENTER PLATFORM TERMINAL", use_container_width=True):
                user_clean = u.strip()
                pass_clean = p.strip()
                
                # Direct Master Check with updated credentials
                if (user_clean.lower() == "parthkirana" and pass_clean == "Parth@1122") or (user_clean.lower() == "admin" and pass_clean == "admin123"):
                    st.session_state.authenticated = True
                    st.session_state.username = user_clean
                    st.session_state.role = "Admin"
                    st.rerun()
                else:
                    try:
                        engine, _ = get_engine()
                        with engine.connect() as conn:
                            result = conn.execute(text("SELECT username, role FROM users WHERE LOWER(username)=:u AND password_hash=:p"),
                                                  {"u": user_clean.lower(), "p": hash_txt(pass_clean)}).fetchone()
                        if result:
                            st.session_state.authenticated = True
                            st.session_state.username = result[0]
                            st.session_state.role = result[1]
                            st.rerun()
                        else:
                            st.error("Invalid Username or Password!")
                    except Exception:
                        st.error("Invalid Credentials!")
        st.info("💡 Login ID: **parthkirana** | Password: **Parth@1122**")
    st.stop()

# --- SIDEBAR ---
engine, current_db_status = get_engine()
st.sidebar.markdown(f"""
<div style='background: rgba(30, 41, 59, 0.5); padding: 16px; border-radius: 14px; border: 1px solid rgba(56, 189, 248, 0.2); margin-bottom: 20px;'>
    <h3 style='color: #38bdf8; margin: 0; font-size: 18px; font-weight: 800;'>⚡ {BIZ_NAME}</h3>
    <div style='margin-top: 10px; font-size: 12px; color: #cbd5e1;'>
        👤 <b>{st.session_state.username}</b> ({st.session_state.role})
        <div style='color: #4ade80; font-size: 11px; margin-top: 4px;'>{current_db_status}</div>
    </div>
</div>
""", unsafe_allow_html=True)

menu_options = ["🛒 Digital POS Billing", "👥 Customer 360° & Udhaar Ledger"]
if st.session_state.role == "Admin":
    menu_options.extend(["📦 Inventory & Stock Control", "📊 Sales & Net Profit Dashboard"])
choice = st.sidebar.radio("Platform Modules", menu_options)

if st.sidebar.button("🚪 Terminate Session (Logout)", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.cart = []
    st.session_state.last_inv = None
    st.rerun()

# --- MODULE 1: POS BILLING (WITH DIRECT MANUAL ITEM ENTRY) ---
if choice == "🛒 Digital POS Billing":
    st.markdown("<h2 class='glass-header'>🛒 Next-Gen Web POS Terminal</h2>", unsafe_allow_html=True)
    col_pos_left, col_pos_right = st.columns([1.55, 1.45], gap="large")
    
    with col_pos_left:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #38bdf8; margin: 0 0 12px 0;'>👤 Customer Details & Lookup</h4>", unsafe_allow_html=True)
        c_col1, c_col2, c_col3 = st.columns([1.5, 1.5, 1.5])
        mob = c_col1.text_input("Mobile Number", max_chars=10, placeholder="10 Digit Number")
        c_name, c_village, old_udhaar = "Cash Customer", "", 0.0
        
        if len(mob) == 10:
            try:
                engine, _ = get_engine()
                with engine.connect() as conn:
                    row = conn.execute(text("SELECT name, village, outstanding_balance FROM customers WHERE mobile=:m"), {"m": mob}).fetchone()
                if row:
                    c_name, c_village, old_udhaar = row[0], row[1] or "", max(0.0, float(row[2]))
                    c_col2.text_input("Customer Name", value=c_name, disabled=True)
                    c_col3.text_input("Village / Area", value=c_village, disabled=True)
                    if old_udhaar > 0:
                        st.markdown(f"<span class='badge-udhaar'>🚨 Past Udhaar: ₹ {old_udhaar:,.2f}</span>", unsafe_allow_html=True)
                else:
                    c_name = c_col2.text_input("Customer Name", value="", placeholder="Enter Name")
                    c_village = c_col3.text_input("Village / Area", value="", placeholder="Enter Village")
            except Exception:
                pass
        else:
            c_col2.text_input("Customer Name", value=c_name, disabled=True)
            c_col3.text_input("Village / Area", value="-", disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # PRODUCT SECTION WITH DIRECT MANUAL ITEM ENTRY
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #38bdf8; margin: 0 0 12px 0;'>📦 Add Wholesale Items</h4>", unsafe_allow_html=True)
        
        item_mode = st.radio("Add Item Via:", ["📦 Inventory Database", "✍️ Direct Manual Entry (Bina Inventory ke)"], horizontal=True)
        
        if item_mode == "📦 Inventory Database":
            try:
                engine, _ = get_engine()
                df_prods = pd.read_sql("SELECT id, name, buy_price, sell_price, stock FROM products ORDER BY name", engine)
            except Exception:
                df_prods = pd.DataFrame(columns=['id', 'name', 'buy_price', 'sell_price', 'stock'])
            
            p_c1, p_c2, p_c3 = st.columns([2.2, 1, 1])
            prod_map = {f"{r['name']} (₹{r['sell_price']} | Stock: {r['stock']})": r['id'] for _, r in df_prods.iterrows()}
            sel_label = p_c1.selectbox("Select Product", ["-- Select Item --"] + list(prod_map.keys()))
            qty = p_c2.number_input("Quantity", min_value=1, value=1, step=1)
            p_c3.markdown("<br>", unsafe_allow_html=True)
            if p_c3.button("➕ Add", use_container_width=True, type="primary"):
                if sel_label != "-- Select Item --":
                    pid = prod_map[sel_label]
                    p_info = df_prods[df_prods['id'] == pid].iloc[0]
                    st.session_state.cart.append({
                        'id': pid,
                        'name': p_info['name'],
                        'buy': p_info['buy_price'],
                        'sell': p_info['sell_price'],
                        'qty': qty,
                        'total': qty * p_info['sell_price'],
                        'profit': qty * (p_info['sell_price'] - p_info['buy_price']),
                        'is_manual': False
                    })
                    st.rerun()
        else:
            # DIRECT MANUAL ENTRY
            m_c1, m_c2, m_c3, m_c4 = st.columns([2.2, 1, 1, 1])
            custom_pname = m_c1.text_input("Item Name (e.g. 250 ml Water Pack)")
            custom_rate = m_c2.number_input("Rate ₹ (per peti/pc)", min_value=1.0, value=140.0, step=10.0)
            custom_qty = m_c3.number_input("Quantity", min_value=1, value=1, step=1)
            m_c4.markdown("<br>", unsafe_allow_html=True)
            if m_c4.button("➕ Add Item", use_container_width=True, type="primary"):
                if custom_pname.strip():
                    st.session_state.cart.append({
                        'id': 0,
                        'name': custom_pname.strip(),
                        'buy': custom_rate,
                        'sell': custom_rate,
                        'qty': custom_qty,
                        'total': custom_qty * custom_rate,
                        'profit': 0.0,
                        'is_manual': True
                    })
                    st.success(f"Added '{custom_pname}'!")
                    st.rerun()
                else:
                    st.error("Item name enter karein!")
                    
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.cart:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("##### 🛒 Current Cart Items")
            df_c = pd.DataFrame(st.session_state.cart)
            st.dataframe(df_c[['name', 'qty', 'sell', 'total']], use_container_width=True, hide_index=True)
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
        m2.metric("Old Udhaar", f"₹ {old_udhaar:,.2f}")
        
        st.markdown(f"<h3 style='color: #38bdf8;'>Net Payable: ₹ {net_payable:,.2f}</h3>", unsafe_allow_html=True)
        paid = st.number_input("Received Cash / UPI (₹)", min_value=0.0, value=float(subtotal), step=50.0)
        remaining_balance = max(0.0, net_payable - paid)
        
        if remaining_balance > 0:
            st.markdown(f"<p style='color: #f87171; font-weight: bold;'>🚨 Remaining Udhaar: ₹ {remaining_balance:,.2f}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #4ade80; font-weight: bold;'>✅ Full Payment Cleared</p>", unsafe_allow_html=True)
            
        if st.button("🚀 SAVE & GENERATE INVOICE SLIP", type="primary", use_container_width=True):
            if not st.session_state.cart:
                st.error("Cart is empty!")
            elif not mob or len(mob) != 10:
                st.error("Valid 10-digit customer mobile number daalein!")
            else:
                now = datetime.now()
                d_str, dt_str = now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d %I:%M %p")
                engine, _ = get_engine()
                with engine.begin() as conn:
                    conn.execute(text("""
                    INSERT INTO invoices (date_time, date, customer_mobile, customer_name, customer_village, subtotal, discount, total_amount, paid_amount, udhaar_amount, total_profit, payment_mode, billed_by)
                    VALUES (:dt, :d, :mob, :name, :vil, :sub, 0.0, :tot, :paid, :udh, :prof, :pmode, :bby);
                    """), {
                        "dt": dt_str, "d": d_str, "mob": mob, "name": c_name or "Customer", "vil": c_village,
                        "sub": float(subtotal), "tot": float(subtotal), "paid": float(paid), "udh": float(remaining_balance), "prof": float(total_profit),
                        "pmode": "UPI/Cash", "bby": st.session_state.username
                    })
                    inv_no = conn.execute(text("SELECT MAX(invoice_no) FROM invoices")).scalar() or 1
                    
                    for it in st.session_state.cart:
                        conn.execute(text("""
                        INSERT INTO invoice_items (invoice_no, product_id, product_name, qty, buy_price, sell_price, total, profit)
                        VALUES (:inv, :pid, :pname, :qty, :buy, :sell, :tot, :prof);
                        """), {
                            "inv": int(inv_no), "pid": int(it['id']), "pname": it['name'], "qty": int(it['qty']),
                            "buy": float(it['buy']), "sell": float(it['sell']), "tot": float(it['total']), "prof": float(it['profit'])
                        })
                        if not it.get('is_manual', False) and it['id'] > 0:
                            conn.execute(text("UPDATE products SET stock = stock - :qty WHERE id=:pid"), {"qty": int(it['qty']), "pid": int(it['id'])})
                    
                    try:
                        conn.execute(text("""
                        INSERT INTO customers (mobile, name, village, outstanding_balance, last_purchase_date, last_purchase_amount)
                        VALUES (:m, :n, :v, :bal, :lpd, :lpa)
                        ON CONFLICT(mobile) DO UPDATE SET
                            name=EXCLUDED.name,
                            village=EXCLUDED.village,
                            outstanding_balance=EXCLUDED.outstanding_balance,
                            last_purchase_date=EXCLUDED.last_purchase_date,
                            last_purchase_amount=EXCLUDED.last_purchase_amount;
                        """), {"m": mob, "n": c_name or "Customer", "v": c_village, "bal": float(remaining_balance), "lpd": d_str, "lpa": float(subtotal)})
                    except Exception:
                        conn.execute(text("UPDATE customers SET outstanding_balance=:bal WHERE mobile=:m"), {"bal": float(remaining_balance), "m": mob})
                        
                st.session_state.last_inv = {
                    'inv_no': inv_no, 'dt': dt_str, 'name': c_name, 'mob': mob, 'village': c_village,
                    'items': st.session_state.cart, 'subtotal': subtotal, 'old_udhaar': old_udhaar, 'paid': paid, 'balance': remaining_balance
                }
                st.session_state.cart = []
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Live Bill Slip + SMS / WhatsApp Triggers
        if st.session_state.last_inv:
            inv = st.session_state.last_inv
            items_html = "".join([f"<tr><td style='padding:4px;'>{it['name']}</td><td style='text-align:center;'>{it['qty']}</td><td style='text-align:right;'>₹{it['sell']:.2f}</td><td style='text-align:right;'>₹{it['total']:.2f}</td></tr>" for it in inv['items']])
            upi_amt = inv['paid'] if inv['paid'] > 0 else (inv['subtotal'] + inv['old_udhaar'])
            qr_src = f"https://api.qrserver.com/v1/create-qr-code/?size=130x130&data=upi://pay?pa={DEFAULT_UPI_ID}%26pn={urllib.parse.quote(BIZ_NAME)}%26am={upi_amt:.2f}%26cu=INR"
            
            receipt_full_html = f"""
            <div style='background:#ffffff; color:#0f172a; padding:15px; border:1px solid #ddd; max-width:380px; margin:auto; border-radius:8px;'>
                <div style='text-align:center; border-bottom:2px dashed #0284c7; padding-bottom:8px;'>
                    <h3 style='margin:0; color:#0284c7;'>⚡ {BIZ_NAME}</h3>
                    <div style='font-size:11px;'>{BIZ_TAGLINE}</div>
                </div>
                <div style='font-size:12px; margin:8px 0;'>
                    <b>Bill No:</b> #{inv['inv_no']} &nbsp;|&nbsp; <b>Date:</b> {inv['dt']}<br>
                    <b>Customer:</b> {inv['name']} ({inv['mob']})
                </div>
                <table style='width:100%; font-size:11px; border-collapse:collapse;'>
                    <thead><tr style='background:#0f172a; color:#ffffff;'><th>Item</th><th>Qty</th><th style='text-align:right;'>Rate</th><th style='text-align:right;'>Total</th></tr></thead>
                    <tbody>{items_html}</tbody>
                </table>
                <div style='margin-top:8px; font-size:12px; border-top:1px solid #ccc; padding-top:6px;'>
                    <div><b>Bill Total:</b> ₹ {inv['subtotal']:.2f}</div>
                    <div>Paid Amount: ₹ {inv['paid']:.2f}</div>
                    <div style='color:#dc2626; font-weight:bold;'>Remaining Udhaar: ₹ {inv['balance']:.2f}</div>
                </div>
                <div style='text-align:center; margin-top:8px;'>
                    <img src='{qr_src}' width='90' height='90'><br>
                    <small>UPI: {DEFAULT_UPI_ID}</small>
                </div>
            </div>
            """
            components.html(f"{receipt_full_html}<div style='text-align:center; margin-top:8px;'><button onclick='window.print()' style='background:#0284c7; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer;'>🖨️ PRINT RECEIPT</button></div>", height=500, scrolling=True)
            
            items_str = "%0A".join([f"• {it['name']} x {it['qty']} = Rs.{it['total']:.2f}" for it in inv['items']])
            msg_wa = f"*⚡ {BIZ_NAME} - INVOICE #{inv['inv_no']}*%0ANamaste *{inv['name']}* ji,%0A{items_str}%0A*Total: Rs.{inv['subtotal']:.2f}*%0APaid: Rs.{inv['paid']:.2f}%0AUdhaar: Rs.{inv['balance']:.2f}"
            wa_url = f"https://api.whatsapp.com/send?phone=91{inv['mob']}&text={msg_wa}"
            sms_text = f"Namaste {inv['name']} ji! {BIZ_NAME} Bill #{inv['inv_no']}: Total Rs.{inv['subtotal']:.2f}, Paid Rs.{inv['paid']:.2f}, Udhaar Rs.{inv['balance']:.2f}."
            sms_url = f"sms:+91{inv['mob']}?body={urllib.parse.quote(sms_text)}"
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown(f"<a href='{sms_url}'><button class='btn-sms'>📲 Send Text SMS</button></a>", unsafe_allow_html=True)
            with col_m2:
                st.markdown(f"<a href='{wa_url}' target='_blank'><button class='btn-wa'>💬 Send WhatsApp</button></a>", unsafe_allow_html=True)

# --- MODULE 2: CUSTOMERS & UDHAAR LEDGER ---
elif choice == "👥 Customer 360° & Udhaar Ledger":
    st.markdown("<h2 class='glass-header'>👥 Customer 360° & Udhaar Ledger</h2>", unsafe_allow_html=True)
    try:
        engine, _ = get_engine()
        df_cust = pd.read_sql("SELECT id, mobile, name, village, outstanding_balance, last_purchase_date, last_purchase_amount FROM customers ORDER BY outstanding_balance DESC", engine)
    except Exception:
        df_cust = pd.DataFrame(columns=['id', 'mobile', 'name', 'village', 'outstanding_balance', 'last_purchase_date', 'last_purchase_amount'])
    
    col_l1, col_l2 = st.columns([1.6, 1.4], gap="large")
    with col_l1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("##### 📋 All Customers Directory")
        st.dataframe(df_cust, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("##### 💵 Quick Udhaar Collection Entry")
        with st.form("rec_pay_form"):
            r_c1, r_c2 = st.columns(2)
            sel_mob = r_c1.selectbox("Select Customer Mobile", df_cust['mobile'].tolist() if not df_cust.empty else ["No Customers"])
            r_amt = r_c2.number_input("Received Amount (₹)", min_value=1.0, step=50.0)
            if st.form_submit_button("Record Udhaar Deposit", use_container_width=True, type="primary"):
                if sel_mob != "No Customers":
                    engine, _ = get_engine()
                    with engine.begin() as conn:
                        c_row = conn.execute(text("SELECT name, outstanding_balance FROM customers WHERE mobile=:m"), {"m": sel_mob}).fetchone()
                        old_bal = c_row[1] if c_row else 0.0
                        new_bal = max(0.0, old_bal - r_amt)
                        conn.execute(text("UPDATE customers SET outstanding_balance = :bal WHERE mobile=:m"), {"bal": new_bal, "m": sel_mob})
                    st.success(f"₹ {r_amt:,.2f} payment recorded for {sel_mob}!")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_l2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("##### 📜 Customer Multi-Bill History")
        target_cust = st.selectbox("Select Customer", options=df_cust['mobile'].tolist() if not df_cust.empty else [])
        if target_cust:
            try:
                engine, _ = get_engine()
                df_invoices = pd.read_sql(f"SELECT invoice_no, date_time, total_amount, paid_amount, udhaar_amount, billed_by FROM invoices WHERE customer_mobile='{target_cust}' ORDER BY invoice_no DESC", engine)
                st.dataframe(df_invoices, use_container_width=True, hide_index=True)
            except Exception:
                st.info("No records found.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- MODULE 3: INVENTORY CONTROL ---
elif choice == "📦 Inventory & Stock Control":
    st.markdown("<h2 class='glass-header'>📦 Wholesale Inventory & Price Control</h2>", unsafe_allow_html=True)
    try:
        engine, _ = get_engine()
        df_prods = pd.read_sql("SELECT id, barcode, name, category, buy_price, sell_price, stock FROM products ORDER BY id DESC", engine)
    except Exception:
        df_prods = pd.DataFrame(columns=['id', 'barcode', 'name', 'category', 'buy_price', 'sell_price', 'stock'])
    st.dataframe(df_prods, use_container_width=True, hide_index=True)

# --- MODULE 4: ANALYTICS & PROFIT ---
elif choice == "📊 Sales & Net Profit Dashboard":
    st.markdown("<h2 class='glass-header'>📊 Financial Analytics & Net Profit</h2>", unsafe_allow_html=True)
    f_date = st.date_input("Select Analysis Date", value=datetime.now())
    d_str = f_date.strftime("%Y-%m-%d")
    sales, profit = 0.0, 0.0
    try:
        engine, _ = get_engine()
        with engine.connect() as conn:
            res = conn.execute(text("SELECT SUM(total_amount), SUM(total_profit) FROM invoices WHERE date=:d"), {"d": d_str}).fetchone()
            sales, profit = (res[0] or 0.0), (res[1] or 0.0)
    except Exception:
        pass
    c1, c2 = st.columns(2)
    c1.metric("Selected Date Sales", f"₹ {sales:,.2f}")
    c2.metric("Date Net Profit", f"₹ {profit:,.2f}")
