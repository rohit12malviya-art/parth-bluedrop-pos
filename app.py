"""
================================================================================
⚡ PARTH BLUEDROP - ENTERPRISE FINTECH WHOLESALE ERP & WEB POS SYSTEM
Architecture: Streamlit + Supabase PostgreSQL Engine (Auto-Mirror Fallback)
Modules:
  1. Next-Gen Web POS Terminal (Inventory + Direct Manual Item Billing)
  2. Customer 360° & Udhaar Ledger (Deposit Tracking, SMS/WA Alerts)
  3. Master Inventory Control (Live Stock, Inward Refill, Price Tuning)
  4. Invoice Archive & Thermal Slip Re-Print
  5. Executive Sales & Net Profit Analytics Dashboard
================================================================================
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

# --- PAGE SETUP ---
st.set_page_config(
    page_title="PARTH BLUEDROP | Fintech Cloud ERP",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GLOBAL FINTECH DESIGN SYSTEM (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Cyber Digital Grid Background */
    .stApp {
        background-color: #07090e !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(2, 132, 199, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.12) 0px, transparent 50%),
            linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px) !important;
        background-size: 100% 100%, 100% 100%, 36px 36px, 36px 36px !important;
        color: #f1f5f9;
    }

    section[data-testid="stSidebar"] {
        background-color: #0a0f1d !important;
        border-right: 1px solid rgba(56, 189, 248, 0.15) !important;
    }

    /* Glassmorphic Cards */
    .glass-card {
        background: rgba(15, 23, 42, 0.72) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.14) !important;
        border-radius: 18px !important;
        padding: 22px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 12px 35px -8px rgba(0, 0, 0, 0.6) !important;
    }

    .glass-header {
        background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.65) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(56, 189, 248, 0.18) !important;
        border-radius: 14px !important;
        padding: 16px 20px !important;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.4) !important;
    }

    .btn-sms {
        background: linear-gradient(135deg, #0284c7 0%, #1d4ed8 100%);
        color: white; border: none; padding: 11px; border-radius: 9px; font-weight: 700; width: 100%; cursor: pointer; text-align: center; display: block; text-decoration: none;
    }
    .btn-wa {
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
        color: white; border: none; padding: 11px; border-radius: 9px; font-weight: 700; width: 100%; cursor: pointer; text-align: center; display: block; text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

# --- SYSTEM SETTINGS & CLOUD DB ---
CLOUD_DB_URL = "postgresql+psycopg2://postgres.bawmdovylsaagnfufjiy:Rohit%4062992@aws-0-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require"
DEFAULT_UPI_ID = "9752162992@ybl"
BIZ_NAME = "PARTH BLUEDROP"
BIZ_TAGLINE = "Wholesale Distributor - Chocolates, Cold Drinks & Water"
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

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS stock_logs (
            id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            product_name TEXT,
            qty_added INTEGER,
            buy_price DOUBLE PRECISION,
            total_cost DOUBLE PRECISION
        );
        """))

try:
    init_db()
except Exception:
    pass

# --- SESSION STATES ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'last_inv' not in st.session_state:
    st.session_state.last_inv = None
if 'lamp_on' not in st.session_state:
    st.session_state.lamp_on = True

# ==============================================================================
# ANIMATED LAMP PULL-STRING AUTHENTICATION GATEWAY
# ==============================================================================
if not st.session_state.authenticated:
    is_on = st.session_state.lamp_on
    bg_color = "#16191f" if is_on else "#08090b"
    shade_bg = "#ffffff" if is_on else "#2e384d"
    shade_glow = "0 0 60px rgba(255, 240, 180, 0.9), 0 0 120px rgba(255, 230, 150, 0.5)" if is_on else "none"
    pole_color = "#cbd5e1" if is_on else "#3f4c6b"
    bead_glow = "0 0 12px #f59e0b" if is_on else "none"

    st.markdown(f"""
    <style>
        .stApp {{
            background: {bg_color} !important;
            transition: all 0.5s ease-in-out;
        }}
        header {{visibility: hidden;}}
        section[data-testid="stSidebar"] {{display: none;}}

        .lamp-box {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin-top: 40px;
        }}
        .lamp-head {{
            width: 180px; height: 90px;
            background: {shade_bg};
            border-top-left-radius: 95px; border-top-right-radius: 95px;
            box-shadow: {shade_glow};
            transition: all 0.4s ease;
        }}
        .lamp-pole {{
            width: 14px; height: 210px;
            background: {pole_color};
            border-radius: 6px;
            transition: all 0.4s ease;
        }}
        .lamp-base {{
            width: 140px; height: 18px;
            background: {pole_color};
            border-radius: 12px;
            margin-top: -6px;
            transition: all 0.4s ease;
        }}
        .lamp-dori-visual {{
            position: relative;
            left: 30px; top: -210px;
            width: 3px; height: 95px;
            background: #cbd5e1;
        }}
        .lamp-dori-bead {{
            width: 18px; height: 18px;
            background: #f59e0b;
            border-radius: 50%;
            position: absolute;
            bottom: -9px; left: -7.5px;
            box-shadow: {bead_glow};
        }}
    </style>
    """, unsafe_allow_html=True)

    c_left, c_right = st.columns([1.1, 1], gap="large")

    with c_left:
        st.markdown(f"""
        <div class="lamp-box">
            <div class="lamp-head"></div>
            <div class="lamp-pole"></div>
            <div class="lamp-base"></div>
            <div class="lamp-dori-visual"><div class="lamp-dori-bead"></div></div>
        </div>
        """, unsafe_allow_html=True)
        
        _, c_pull_btn, _ = st.columns([0.8, 2.4, 0.8])
        with c_pull_btn:
            btn_txt = "💡 Dori Khinchein (Light OFF)" if is_on else "💡 Dori Khinchein (Light ON)"
            if st.button(btn_txt, use_container_width=True):
                st.session_state.lamp_on = not st.session_state.lamp_on
                st.rerun()

    with c_right:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if is_on:
            st.markdown("""
            <div style='text-align: center; margin-bottom: 20px;'>
                <h2 style='color: #f8fafc; font-weight: 800; margin: 0; font-size: 28px;'>Welcome</h2>
                <p style='color: #94a3b8; font-size: 13px; margin-top: 4px;'>PARTH BLUEDROP POS Terminal</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("lamp_login_form"):
                u = st.text_input("Username", value="parthkirana", placeholder="Enter username")
                p = st.text_input("Password", type="password", value="Parth@1122", placeholder="Enter password")
                btn_login = st.form_submit_button("🚀 Enter POS Terminal", use_container_width=True)
                
                if btn_login:
                    user_clean = u.strip()
                    pass_clean = p.strip()
                    if (user_clean.lower() == "parthkirana" and pass_clean == "Parth@1122") or (user_clean.lower() == "admin" and pass_clean == "admin123"):
                        st.session_state.authenticated = True
                        st.session_state.username = user_clean
                        st.session_state.role = "Admin"
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password!")
        else:
            st.markdown("""
            <div style='text-align: center; padding: 60px 20px; color: #475569;'>
                <h3 style='color: #334155;'>🌙 Light Band Hai</h3>
                <p style='font-size: 13px;'>Bayein taraf 'Dori Khinchein' par click karein aur lamp on karein.</p>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# SIDEBAR NAVIGATION & STATUS
# ==============================================================================
engine, current_db_status = get_engine()
st.sidebar.markdown(f"""
<div style='background: rgba(30, 41, 59, 0.5); padding: 18px; border-radius: 14px; border: 1px solid rgba(56, 189, 248, 0.2); margin-bottom: 20px;'>
    <div style='font-size: 20px; font-weight: 800; color: #38bdf8;'>⚡ {BIZ_NAME}</div>
    <div style='font-size: 11px; color: #94a3b8; margin-top: 2px;'>{BIZ_TAGLINE}</div>
    <div style='margin-top: 12px; padding-top: 8px; border-top: 1px solid #1e293b; font-size: 12px; color: #cbd5e1;'>
        👤 <b>{st.session_state.username}</b> ({st.session_state.role})
        <div style='color: #4ade80; font-size: 11px; margin-top: 4px;'>{current_db_status}</div>
    </div>
</div>
""", unsafe_allow_html=True)

menu_options = [
    "🛒 Digital POS Billing", 
    "👥 Customer 360° & Udhaar Ledger",
    "📦 Inventory & Stock Control",
    "📜 Invoice History & Re-Print",
    "📊 Financial Analytics & Net Profit"
]
choice = st.sidebar.radio("Platform Modules", menu_options)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Terminate Session (Logout)", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.cart = []
    st.session_state.last_inv = None
    st.rerun()


# ==============================================================================
# MODULE 1: DIGITAL POS TERMINAL (INVENTORY + DIRECT MANUAL ITEM ENTRY)
# ==============================================================================
if choice == "🛒 Digital POS Billing":
    st.markdown("<h2 class='glass-header'>🛒 Enterprise Web POS Terminal</h2>", unsafe_allow_html=True)
    col_pos_left, col_pos_right = st.columns([1.55, 1.45], gap="large")
    
    with col_pos_left:
        # Customer Card
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #38bdf8; margin: 0 0 12px 0;'>👤 Customer Lookup & Profiling</h4>", unsafe_allow_html=True)
        c_col1, c_col2, c_col3 = st.columns([1.5, 1.5, 1.5])
        mob = c_col1.text_input("Mobile Number", max_chars=10, placeholder="10 Digit Mobile")
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
                        st.markdown(f"<span style='background:#dc2626; color:white; padding:4px 12px; border-radius:15px; font-size:12px; font-weight:bold;'>🚨 Past Udhaar Due: ₹ {old_udhaar:,.2f}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='background:#059669; color:white; padding:4px 12px; border-radius:15px; font-size:12px; font-weight:bold;'>✅ Clean Balance (No Udhaar)</span>", unsafe_allow_html=True)
                else:
                    c_name = c_col2.text_input("Customer Name", value="", placeholder="Enter Name")
                    c_village = c_col3.text_input("Village / Area", value="", placeholder="Enter Village")
                    st.caption("✨ New Customer Auto-Register")
            except Exception:
                pass
        else:
            c_col2.text_input("Customer Name", value=c_name, disabled=True)
            c_col3.text_input("Village / Area", value="-", disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Products Section with Direct Manual / Custom Entry
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #38bdf8; margin: 0 0 12px 0;'>📦 Add Wholesale Products</h4>", unsafe_allow_html=True)
        
        item_mode = st.radio("Add Method:", ["📦 Saved Inventory Product", "✍️ Direct Manual Item (Bina Inventory ke)"], horizontal=True)
        
        if item_mode == "📦 Saved Inventory Product":
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
            if p_c3.button("➕ Add Item", use_container_width=True, type="primary"):
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
            # DIRECT CUSTOM ENTRY
            m_c1, m_c2, m_c3, m_c4 = st.columns([2.2, 1, 1, 1])
            custom_pname = m_c1.text_input("Item Name (e.g. 250 ml Water Pack)")
            custom_rate = m_c2.number_input("Rate ₹ (per peti/pc)", min_value=1.0, value=140.0, step=10.0)
            custom_qty = m_c3.number_input("Quantity", min_value=1, value=1, step=1)
            m_c4.markdown("<br>", unsafe_allow_html=True)
            if m_c4.button("➕ Add Manual", use_container_width=True, type="primary"):
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

        # Cart View
        if st.session_state.cart:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("##### 🛒 Active Invoice Cart")
            df_c = pd.DataFrame(st.session_state.cart)
            st.dataframe(
                df_c[['name', 'qty', 'sell', 'total']],
                column_config={"name": "Product Name", "qty": "Quantity", "sell": "Rate (₹)", "total": "Total (₹)"},
                use_container_width=True, hide_index=True
            )
            if st.button("🗑️ Clear Entire Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    with col_pos_right:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #38bdf8; margin: 0 0 12px 0;'>💰 Payment Calculation & Billing</h4>", unsafe_allow_html=True)
        
        subtotal = sum(it['total'] for it in st.session_state.cart)
        total_profit = sum(it['profit'] for it in st.session_state.cart)
        net_payable = subtotal + old_udhaar
        
        m1, m2 = st.columns(2)
        m1.metric("Current Bill", f"₹ {subtotal:,.2f}")
        m2.metric("Old Udhaar Due", f"₹ {old_udhaar:,.2f}", delta=f"-₹ {old_udhaar:.2f}" if old_udhaar > 0 else None, delta_color="inverse")
        
        st.markdown(f"<h3 style='color: #38bdf8; margin: 10px 0;'>Total Net Due: ₹ {net_payable:,.2f}</h3>", unsafe_allow_html=True)
        paid = st.number_input("Received Cash / UPI (₹)", min_value=0.0, value=float(subtotal), step=50.0)
        remaining_balance = max(0.0, net_payable - paid)
        
        if remaining_balance > 0:
            st.markdown(f"<p style='color: #f87171; font-weight: bold; font-size: 15px;'>🚨 Remaining Udhaar: ₹ {remaining_balance:,.2f}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #4ade80; font-weight: bold; font-size: 15px;'>✅ Full Payment Cleared</p>", unsafe_allow_html=True)
            
        if st.button("🚀 SAVE & GENERATE INVOICE SLIP", type="primary", use_container_width=True):
            if not st.session_state.cart:
                st.error("Cart is empty! Add products first.")
            elif not mob or len(mob) != 10:
                st.error("Enter valid 10-digit customer mobile number!")
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
        
        # Live Bill Slip
        if st.session_state.last_inv:
            inv = st.session_state.last_inv
            items_html = "".join([f"<tr><td style='padding:5px; border-bottom:1px dashed #cbd5e1;'>{it['name']}</td><td style='text-align:center; padding:5px; border-bottom:1px dashed #cbd5e1;'>{it['qty']}</td><td style='text-align:right; padding:5px; border-bottom:1px dashed #cbd5e1;'>₹{it['sell']:.2f}</td><td style='text-align:right; padding:5px; border-bottom:1px dashed #cbd5e1; font-weight:bold;'>₹{it['total']:.2f}</td></tr>" for it in inv['items']])
            upi_amt = inv['paid'] if inv['paid'] > 0 else (inv['subtotal'] + inv['old_udhaar'])
            qr_src = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=upi://pay?pa={DEFAULT_UPI_ID}%26pn={urllib.parse.quote(BIZ_NAME)}%26am={upi_amt:.2f}%26cu=INR"
            
            receipt_full_html = f"""
            <div style='background:#ffffff; color:#0f172a; padding:18px; border:1px solid #ddd; max-width:380px; margin:auto; border-radius:10px; font-family:Arial,sans-serif;'>
                <div style='text-align:center; border-bottom:2px dashed #0284c7; padding-bottom:8px;'>
                    <h3 style='margin:0; color:#0284c7;'>⚡ {BIZ_NAME}</h3>
                    <div style='font-size:11px;'>{BIZ_TAGLINE}</div>
                    <div style='font-size:10px; color:#64748b;'>{BIZ_ADDRESS}<br>Phone: {BIZ_PHONE}</div>
                </div>
                <div style='font-size:12px; margin:10px 0;'>
                    <b>Bill No:</b> #{inv['inv_no']} &nbsp;|&nbsp; <b>Date:</b> {inv['dt']}<br>
                    <b>Customer:</b> {inv['name']} ({inv['mob']})<br>
                    <b>Village:</b> {inv['village'] or 'N/A'}
                </div>
                <table style='width:100%; font-size:11px; border-collapse:collapse;'>
                    <thead><tr style='background:#0f172a; color:#ffffff;'><th>Item</th><th>Qty</th><th style='text-align:right;'>Rate</th><th style='text-align:right;'>Total</th></tr></thead>
                    <tbody>{items_html}</tbody>
                </table>
                <div style='margin-top:10px; font-size:12px; border-top:1px solid #ccc; padding-top:6px; line-height:1.5;'>
                    <div><b>Bill Total:</b> ₹ {inv['subtotal']:.2f}</div>
                    <div>Purana Udhaar: ₹ {inv['old_udhaar']:.2f}</div>
                    <div style='color:#059669; font-weight:bold;'>Paid: ₹ {inv['paid']:.2f}</div>
                    <div style='color:#dc2626; font-weight:bold;'>Remaining Udhaar: ₹ {inv['balance']:.2f}</div>
                </div>
                <div style='text-align:center; margin-top:10px; border-top:1px dashed #ccc; padding-top:6px;'>
                    <img src='{qr_src}' width='95' height='95'><br>
                    <small style='font-size:10px;'>Scan & Pay UPI: {DEFAULT_UPI_ID}</small>
                </div>
            </div>
            """
            components.html(f"{receipt_full_html}<div style='text-align:center; margin-top:10px;'><button onclick='window.print()' style='background:#0284c7; color:white; border:none; padding:10px 20px; font-weight:bold; border-radius:6px; cursor:pointer;'>🖨️ PRINT RECEIPT</button></div>", height=540, scrolling=True)
            
            items_str = "%0A".join([f"• {it['name']} x {it['qty']} = Rs.{it['total']:.2f}" for it in inv['items']])
            msg_wa = f"*⚡ {BIZ_NAME} - INVOICE #{inv['inv_no']}*%0ANamaste *{inv['name']}* ji,%0A{items_str}%0A*Total: Rs.{inv['subtotal']:.2f}*%0A*Purana Udhaar: Rs.{inv['old_udhaar']:.2f}*%0APaid: Rs.{inv['paid']:.2f}%0A*Remaining Udhaar: Rs.{inv['balance']:.2f}*%0A_Dhanyawad! {BIZ_NAME}_"
            wa_url = f"https://api.whatsapp.com/send?phone=91{inv['mob']}&text={msg_wa}"
            sms_text = f"Namaste {inv['name']} ji! {BIZ_NAME} Bill #{inv['inv_no']}: Total Rs.{inv['subtotal']:.2f}, Paid Rs.{inv['paid']:.2f}, Udhaar Rs.{inv['balance']:.2f}. Dhanyawad!"
            sms_url = f"sms:+91{inv['mob']}?body={urllib.parse.quote(sms_text)}"
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown(f"<a href='{sms_url}'><button class='btn-sms'>📲 Send Text SMS</button></a>", unsafe_allow_html=True)
            with col_m2:
                st.markdown(f"<a href='{wa_url}' target='_blank'><button class='btn-wa'>💬 Send WhatsApp</button></a>", unsafe_allow_html=True)


# ==============================================================================
# MODULE 2: CUSTOMER 360° & MULTI-BILL LEDGER
# ==============================================================================
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
        st.markdown("##### 📋 Customer Directory & Balances")
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
            use_container_width=True, hide_index=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("##### 💵 Receive Udhaar Payment")
        with st.form("rec_pay_form"):
            r_c1, r_c2 = st.columns(2)
            sel_mob = r_c1.selectbox("Select Customer", df_cust['mobile'].tolist() if not df_cust.empty else ["No Customers"])
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
        st.markdown("##### 📜 Customer Account History")
        target_cust = st.selectbox("Select Customer to Inspect", options=df_cust['mobile'].tolist() if not df_cust.empty else [])
        if target_cust:
            try:
                engine, _ = get_engine()
                df_invoices = pd.read_sql(f"SELECT invoice_no, date_time, total_amount, paid_amount, udhaar_amount, billed_by FROM invoices WHERE customer_mobile='{target_cust}' ORDER BY invoice_no DESC", engine)
                st.dataframe(
                    df_invoices,
                    column_config={
                        "invoice_no": "Inv #",
                        "date_time": "Date",
                        "total_amount": st.column_config.NumberColumn("Total (₹)", format="₹ %.2f"),
                        "paid_amount": st.column_config.NumberColumn("Paid (₹)", format="₹ %.2f"),
                        "udhaar_amount": st.column_config.NumberColumn("Udhaar (₹)", format="₹ %.2f")
                    },
                    use_container_width=True, hide_index=True
                )
            except Exception:
                st.info("No records found.")
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# MODULE 3: MASTER INVENTORY CONTROL (REGISTER NEW + REFILL + EDIT)
# ==============================================================================
elif choice == "📦 Inventory & Stock Control":
    st.markdown("<h2 class='glass-header'>📦 Master Inventory, Re-Stock & Price Control</h2>", unsafe_allow_html=True)
    
    try:
        engine, _ = get_engine()
        df_prods = pd.read_sql("SELECT id, barcode, name, category, buy_price, sell_price, stock FROM products ORDER BY id DESC", engine)
        df_stock_in = pd.read_sql("SELECT date, product_name, qty_added, buy_price, total_cost FROM stock_logs ORDER BY id DESC LIMIT 50", engine)
    except Exception:
        df_prods = pd.DataFrame(columns=['id', 'barcode', 'name', 'category', 'buy_price', 'sell_price', 'stock'])
        df_stock_in = pd.DataFrame(columns=['date', 'product_name', 'qty_added', 'buy_price', 'total_cost'])

    t1, t2, t3 = st.tabs(["⚡ Quick Refill & Edit", "➕ Register Brand New Product", "📦 Stock List & Valuation"])

    with t1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("#### ⚡ 1-Click Stock Refill (Maal Aane par)")
        if not df_prods.empty:
            prod_dict = {f"#{r['id']} - {r['name']} (Stock: {r['stock']} | Buy: ₹{r['buy_price']} | Sell: ₹{r['sell_price']})": r['id'] for _, r in df_prods.iterrows()}
            selected_item_label = st.selectbox("Select Product to Refill", list(prod_dict.keys()))
            selected_id = prod_dict[selected_item_label]
            p_data = df_prods[df_prods['id'] == selected_id].iloc[0]

            c_act1, c_act2 = st.columns(2, gap="large")
            with c_act1:
                st.markdown("##### ➕ Incoming Stock Units")
                with st.form("refill_form"):
                    add_qty = st.number_input("Incoming Units (Boxes/Pieces)", min_value=1, value=10, step=5)
                    b_rate = st.number_input("Purchase Rate for this Batch ₹", min_value=0.0, value=float(p_data['buy_price']), step=5.0)
                    if st.form_submit_button("🚀 Add Stock & Log", type="primary", use_container_width=True):
                        engine, _ = get_engine()
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE products SET stock = stock + :qty, buy_price = :rate WHERE id = :pid"),
                                         {"qty": add_qty, "rate": b_rate, "pid": selected_id})
                            conn.execute(text("INSERT INTO stock_logs (date, product_name, qty_added, buy_price, total_cost) VALUES (:d, :pname, :qty, :rate, :cost)"),
                                         {"d": datetime.now().strftime("%Y-%m-%d"), "pname": p_data['name'], "qty": add_qty, "rate": b_rate, "cost": add_qty * b_rate})
                        st.success(f"Added {add_qty} units to {p_data['name']}!")
                        st.rerun()

            with c_act2:
                st.markdown("##### ✏️ Tune Product Details")
                with st.form("edit_prod_form"):
                    e_name = st.text_input("Product Name", value=p_data['name'])
                    e_buy = st.number_input("Buy Rate ₹", min_value=0.0, value=float(p_data['buy_price']), step=5.0)
                    e_sell = st.number_input("Sell Rate ₹", min_value=0.0, value=float(p_data['sell_price']), step=5.0)
                    e_stock = st.number_input("Force Set Exact Stock", min_value=0, value=int(p_data['stock']), step=1)
                    if st.form_submit_button("💾 Save Changes", use_container_width=True):
                        engine, _ = get_engine()
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE products SET name=:n, buy_price=:buy, sell_price=:sell, stock=:stk WHERE id=:pid"),
                                         {"n": e_name, "buy": e_buy, "sell": e_sell, "stk": e_stock, "pid": selected_id})
                        st.success("Product updated!")
                        st.rerun()
        else:
            st.info("No products found. Register a product in the next tab.")
        st.markdown("</div>", unsafe_allow_html=True)

    with t2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("#### ➕ Add New Wholesale Product into Inventory")
        with st.form("add_new_prod_full"):
            n_c1, n_c2 = st.columns(2)
            pname = n_c1.text_input("Product Name * (e.g. 250 ml Water Pack / Dairy Milk)")
            pcat = n_c1.selectbox("Category", ["Water & Beverages", "Chocolate Wholesale", "Cold Drinks", "Snacks & Others"])
            bcode = n_c1.text_input("Barcode / Item Code (Optional)")
            
            bprice = n_c2.number_input("Purchase / Buy Rate ₹", min_value=0.0, step=5.0)
            sprice = n_c2.number_input("Wholesale Sell Rate ₹", min_value=0.0, step=5.0)
            pstock = n_c2.number_input("Opening Stock Units", min_value=0, value=50, step=10)
            
            if st.form_submit_button("🚀 Save New Product to Inventory", use_container_width=True, type="primary"):
                if pname.strip():
                    clean_bcode = bcode.strip() if bcode.strip() else None
                    engine, _ = get_engine()
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO products (barcode, name, category, buy_price, sell_price, stock) VALUES (:b, :n, :c, :buy, :sell, :stk)"),
                                     {"b": clean_bcode, "n": pname.strip(), "c": pcat, "buy": bprice, "sell": sprice, "stk": pstock})
                        conn.execute(text("INSERT INTO stock_logs (date, product_name, qty_added, buy_price, total_cost) VALUES (:d, :pname, :qty, :buy, :cost)"),
                                     {"d": datetime.now().strftime("%Y-%m-%d"), "pname": pname.strip(), "qty": pstock, "buy": bprice, "cost": pstock * bprice})
                    st.success(f"Successfully registered '{pname}'!")
                    st.rerun()
                else:
                    st.error("Product name cannot be empty!")
        st.markdown("</div>", unsafe_allow_html=True)

    with t3:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("#### 📦 Master Stock Inventory Directory")
        st.dataframe(
            df_prods,
            column_config={
                "id": "Item ID",
                "name": "Product Description",
                "category": "Category",
                "buy_price": st.column_config.NumberColumn("Buy Price (₹)", format="₹ %.2f"),
                "sell_price": st.column_config.NumberColumn("Sell Price (₹)", format="₹ %.2f"),
                "stock": st.column_config.NumberColumn("Stock Balance", format="%d units")
            },
            use_container_width=True, hide_index=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# MODULE 4: INVOICE HISTORY & THERMAL RE-PRINT
# ==============================================================================
elif choice == "📜 Invoice History & Re-Print":
    st.markdown("<h2 class='glass-header'>📜 Invoice Archive, Re-Print & WhatsApp Dispatch</h2>", unsafe_allow_html=True)
    
    try:
        engine, _ = get_engine()
        df_all_inv = pd.read_sql("SELECT invoice_no, date_time, customer_name, customer_mobile, customer_village, subtotal, paid_amount, udhaar_amount, total_profit, billed_by FROM invoices ORDER BY invoice_no DESC", engine)
    except Exception:
        df_all_inv = pd.DataFrame()

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("##### 🔍 All Historical Invoices")
    st.dataframe(
        df_all_inv,
        column_config={
            "invoice_no": "Invoice #",
            "date_time": "Timestamp",
            "customer_name": "Customer",
            "customer_mobile": "Mobile",
            "customer_village": "Village",
            "subtotal": st.column_config.NumberColumn("Total Bill (₹)", format="₹ %.2f"),
            "paid_amount": st.column_config.NumberColumn("Paid (₹)", format="₹ %.2f"),
            "udhaar_amount": st.column_config.NumberColumn("Udhaar (₹)", format="₹ %.2f"),
            "billed_by": "Operator"
        },
        use_container_width=True, hide_index=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if not df_all_inv.empty:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("##### 🖨️ Re-Print / WhatsApp Any Invoice")
        sel_inv = st.selectbox("Select Invoice Number", options=df_all_inv['invoice_no'].tolist())
        if sel_inv:
            inv_row = df_all_inv[df_all_inv['invoice_no'] == sel_inv].iloc[0]
            engine, _ = get_engine()
            df_items = pd.read_sql(f"SELECT product_name, qty, sell_price, total FROM invoice_items WHERE invoice_no={sel_inv}", engine)
            
            items_txt = "%0A".join([f"• {r['product_name']} x {r['qty']} = Rs.{r['total']:.2f}" for _, r in df_items.iterrows()])
            wa_resend = f"*⚡ {BIZ_NAME} - RE-PRINT INVOICE #{inv_row['invoice_no']}*%0ANamaste *{inv_row['customer_name']}* ji,%0A{items_txt}%0A*Total: Rs.{inv_row['subtotal']:.2f}*%0APaid: Rs.{inv_row['paid_amount']:.2f}%0AUdhaar: Rs.{inv_row['udhaar_amount']:.2f}%0A_Dhanyawad! {BIZ_NAME}_"
            wa_url_re = f"https://api.whatsapp.com/send?phone=91{inv_row['customer_mobile']}&text={wa_resend}"
            
            c_r1, c_r2 = st.columns(2)
            with c_r1:
                st.markdown(f"<a href='{wa_url_re}' target='_blank'><button class='btn-wa'>💬 Re-Send on WhatsApp</button></a>", unsafe_allow_html=True)
            with c_r2:
                items_html_re = "".join([f"<tr><td style='padding:5px; border-bottom:1px dashed #ccc;'>{r['product_name']}</td><td style='text-align:center; padding:5px; border-bottom:1px dashed #ccc;'>{r['qty']}</td><td style='text-align:right; padding:5px; border-bottom:1px dashed #ccc;'>₹{r['sell_price']:.2f}</td><td style='text-align:right; padding:5px; border-bottom:1px dashed #ccc;'>₹{r['total']:.2f}</td></tr>" for _, r in df_items.iterrows()])
                reprint_html = f"""
                <div style='background:#fff; color:#0f172a; padding:15px; border:1px solid #ddd; max-width:360px; margin:auto; border-radius:8px; font-family:Arial;'>
                    <h3 style='margin:0; text-align:center; color:#0284c7;'>⚡ {BIZ_NAME}</h3>
                    <div style='text-align:center; font-size:10px;'>{BIZ_ADDRESS}</div>
                    <div style='font-size:11px; margin:8px 0;'><b>Inv #{inv_row['invoice_no']}</b> | {inv_row['date_time']}<br>Customer: {inv_row['customer_name']} ({inv_row['customer_mobile']})</div>
                    <table style='width:100%; font-size:10px; border-collapse:collapse;'>{items_html_re}</table>
                    <div style='font-size:11px; margin-top:8px; border-top:1px solid #ccc; padding-top:4px;'>
                        <b>Total: ₹ {inv_row['subtotal']:.2f}</b> | Paid: ₹ {inv_row['paid_amount']:.2f} | Udhaar: ₹ {inv_row['udhaar_amount']:.2f}
                    </div>
                </div>
                """
                components.html(f"{reprint_html}<div style='text-align:center; margin-top:8px;'><button onclick='window.print()' style='background:#0284c7; color:white; border:none; padding:8px 16px; border-radius:6px; font-weight:bold; cursor:pointer;'>🖨️ Thermal Print</button></div>", height=320)
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# MODULE 5: EXECUTIVE ANALYTICS & NET PROFIT DASHBOARD
# ==============================================================================
elif choice == "📊 Financial Analytics & Net Profit":
    st.markdown("<h2 class='glass-header'>📊 Financial Analytics & Net Profit Engine</h2>", unsafe_allow_html=True)
    f_date = st.date_input("Select Analysis Date", value=datetime.now())
    d_str = f_date.strftime("%Y-%m-%d")
    
    sales, profit, mkt_udh = 0.0, 0.0, 0.0
    try:
        engine, _ = get_engine()
        with engine.connect() as conn:
            res = conn.execute(text("SELECT SUM(total_amount), SUM(total_profit) FROM invoices WHERE date=:d"), {"d": d_str}).fetchone()
            sales, profit = (res[0] or 0.0), (res[1] or 0.0)
            res_udh = conn.execute(text("SELECT SUM(outstanding_balance) FROM customers WHERE outstanding_balance > 0")).fetchone()
            mkt_udh = res_udh[0] or 0.0
    except Exception:
        pass
        
    c1, c2, c3 = st.columns(3)
    c1.metric("Daily Sales Volume", f"₹ {sales:,.2f}")
    c2.metric("Daily Net Profit (शुद्ध मुनाफा)", f"₹ {profit:,.2f}")
    c3.metric("Total Market Udhaar Due", f"₹ {mkt_udh:,.2f}")
