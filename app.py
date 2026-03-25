import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ollama
import time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import json
import random
from plyer import notification

# ================= DATABASE IMPORTS =================
from Database.user_service import register_user, authenticate_user, get_user, update_balance
from Database.transaction_service import add_transaction as db_add_transaction, get_transactions
from Database.chat_service import save_chat
from Database.chat_service import save_chat, get_chat_history
from Database.chat_service import delete_chat_session
from Database.transaction_service import (
    add_transaction,
    get_transactions,
    get_monthly_transactions
)
# ================= SECURITY & OTP =================
from utils.security_utils import hash_password, verify_password

# ---------------- BANKING AI JSON LIBRARY ----------------
@st.cache_data
def load_banking_ai_library():
    with open("banking_ai_library.json", "r", encoding="utf-8") as f:
        return json.load(f)

bank_ai = load_banking_ai_library()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="NeoBank AI | Digital Banking",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- SESSION DEFAULTS ----------------
if "initialized" not in st.session_state:
    st.session_state.update({
        "initialized": True,
        "logged_in": False,
        "current_user": None,
        "users": {"demo": {"pass": "demo123", "name": "Nitin Singh", "bal": 125000.0}},
        "show_register": False,
        "chat_history": {},
        "current_chat": None,
        "ai_enabled": True,
        "otp_sent": False,
        "generated_otp": None,
        "temp_user": None,
        "page": "Dashboard",
        "transactions": pd.DataFrame([
            {"Date": "2026-02-01", "Category": "Income", "Type": "Salary", "Amount": 50000.0},
            {"Date": "2026-02-05", "Category": "Food", "Type": "Zomato", "Amount": -1200.0},
            {"Date": "2026-02-08", "Category": "Shopping", "Type": "Amazon", "Amount": -4500.0},
            {"Date": "2026-02-12", "Category": "Bills", "Type": "Electricity", "Amount": -3200.0},
            {"Date": "2026-02-15", "Category": "Travel", "Type": "Uber", "Amount": -800.0}
        ]),
        "cards": {
            "debit": {"active": True, "num": "4532 •••• •••• 8892", "expiry": "12/28"},
            "credit": {"active": True, "num": "5241 •••• •••• 1104", "expiry": "05/29"}
        }
    })

# ---------------- STYLING (Glassmorphism) ----------------
st.markdown("""
<style>
/* ---------------- GLOBAL ---------------- */
.stApp {
    background-color: #0b0e14;
    color: #e2e8f0;
}

[data-testid="stSidebar"] {
    background-color: #111827 !important;
    border-right: 1px solid #1f2937;
}

/* ---------------- CARDS ---------------- */
.glass-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 20px;
    border-radius: 15px;
    backdrop-filter: blur(10px);
    margin-bottom: 20px;
}

.bank-card {
    padding: 20px;
    border-radius: 15px;
    color: white;
    min-height: 170px;
    position: relative;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    margin-bottom: 10px;
    transition: 0.3s;
}

.card-blocked {
    filter: grayscale(1) brightness(0.5);
}

.card-label {
    font-size: 10px;
    text-transform: uppercase;
    opacity: 0.7;
}

/* ---------------- CHAT BUBBLES ---------------- */
.user-bubble {
    background: #2563eb;
    color: white;
    padding: 12px 16px;
    border-radius: 15px 15px 2px 15px;
    margin: 10px 0 10px auto;
    max-width: 75%;
    word-wrap: break-word;
}

.bot-bubble {
    background: #1f2937;
    color: #f1f5f9;
    padding: 12px 16px;
    border-radius: 15px 15px 15px 2px;
    margin: 10px auto 10px 0;
    max-width: 75%;
    border: 1px solid #374151;
    word-wrap: break-word;
}

/* ---------------- SIDEBAR PROFILE ---------------- */
.profile-box {
    background: linear-gradient(145deg, #111827, #0f172a);
    padding: 18px;
    border-radius: 16px;
    border: 1px solid #1f2937;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    margin-bottom: 15px;
}

/* ---------------- LOGIN PAGE ---------------- */
.login-card {
    background: linear-gradient(145deg,#0f172a,#020617);
    border: 1px solid #1f2937;
    padding: 40px;
    border-radius: 22px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.8);
}

.login-title {
    text-align: center;
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 10px;
}

.login-subtitle {
    text-align: center;
    font-size: 14px;
    opacity: 0.6;
    margin-bottom: 25px;
}

/* ---------------- BUTTONS (FIXED SCOPE) ---------------- */
/* Apply style ONLY to quick-action buttons */
div[data-testid="column"] > div > button {
    border-radius: 12px;
    font-size: 14px;
    height: 42px;
    transition: 0.2s ease-in-out;
}

div[data-testid="column"] > div > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(37,99,235,0.35);
}

/* ---------------- CHAT ANIMATION ---------------- */
.user-bubble,
.bot-bubble {
    animation: fadeIn 0.25s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIC HELPERS ----------------
def get_card_ui(card_type, info):

    username = st.session_state.get("current_user")

    # 🔄 Safe user name fetch (DB first, session fallback)
    if username:
        db_user = get_user(username)
        card_holder_name = db_user["full_name"] if db_user else "User"
    else:
        card_holder_name = "User"

    # 🔒 Safe key access
    active = info.get("active", False)
    number = info.get("num", "XXXX •••• •••• XXXX")
    expiry = info.get("expiry", "MM/YY")

    active_status = "ACTIVE" if active else "BLOCKED"
    block_style = "" if active else "card-blocked"

    bg = (
        "linear-gradient(135deg, #1e40af, #3b82f6)"
        if card_type == "debit"
        else "linear-gradient(135deg, #581c87, #a855f7)"
    )

    return f"""
    <div class="bank-card {block_style}" style="background: {bg};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <span style="font-weight: bold; font-size: 14px;">{card_type.upper()} PLATINUM</span>
            <span style="background: rgba(0,0,0,0.4); font-size: 9px; padding: 2px 6px; border-radius: 4px;">{active_status}</span>
        </div>
        <div style="margin-top: 25px; font-size: 18px; letter-spacing: 2px;">{number}</div>
        <div style="margin-top: 25px; display: flex; justify-content: space-between;">
            <div>
                <div class="card-label">Card Holder</div>
                <div style="font-size: 12px;">{card_holder_name}</div>
            </div>
            <div>
                <div class="card-label">Expires</div>
                <div style="font-size: 12px;">{expiry}</div>
            </div>
        </div>
    </div>
    """
def add_transaction(category, tx_type, amount):

    username = st.session_state.get("current_user")

    if not username:
        return

    # 🔹 Create transaction object
    new_tx = {
        "username": username,
        "date": datetime.now(),
        "category": category,
        "type": tx_type,
        "amount": float(amount)
    }

    # 🔥 1️⃣ Save in MongoDB (FIXED)
    from Database.db import transactions_collection
    transactions_collection.insert_one(new_tx)

    # 🔥 2️⃣ Update Session DataFrame (for instant UI update)
    session_tx = {
        "Date": new_tx["date"].strftime("%Y-%m-%d %H:%M"),
        "Category": category,
        "Type": tx_type,
        "Amount": float(amount)
    }

    if "transactions" not in st.session_state:
        st.session_state.transactions = pd.DataFrame(
            columns=["Date", "Category", "Type", "Amount"]
        )

    st.session_state.transactions = pd.concat(
        [st.session_state.transactions, pd.DataFrame([session_tx])],
        ignore_index=True
    )

def offline_bank_reply(message):

    msg = message.lower()
    username = st.session_state.get("current_user")

    if not username:
        return "⚠️ User not logged in."

    # 🔄 Always get fresh user from DB
    db_user = get_user(username)

    if not db_user:
        return "⚠️ User not found."

    current_balance = db_user["balance"]

    # ---------------- BALANCE ----------------
    if "balance" in msg:
        return f"💰 Your balance is ₹{current_balance:,.2f}"

    # ---------------- CARD STATUS ----------------
    if "card" in msg:
        debit = "Active ✅" if st.session_state.cards["debit"]["active"] else "Blocked ❌"
        credit = "Active ✅" if st.session_state.cards["credit"]["active"] else "Blocked ❌"
        return f"💳 Debit Card: {debit}\n💳 Credit Card: {credit}"

    # ---------------- LOAN / EMI ----------------
    if "loan" in msg or "emi" in msg:
        return "🏦 EMI: ₹12,500/month | Loan Outstanding: ₹3,50,000"

    # ---------------- ADD MONEY ----------------
    if "add" in msg or "deposit" in msg:

        amount = "".join(ch for ch in msg if ch.isdigit())

        if not amount:
            return "💡 Example: add 5000"

        amount = int(amount)

        if amount <= 0:
            return "❌ Enter a valid amount."

        # ✅ Calculate new balance properly
        new_balance = current_balance + amount

        # ✅ Update DB correctly
        update_balance(username, new_balance)

        # ✅ Add transaction
        add_transaction(
            category="Income",
            tx_type="Chat Deposit",
            amount=amount
        )

        # 🔄 Refresh session
        st.session_state.users[username]["bal"] = new_balance

        return (
            f"✅ ₹{amount:,.2f} added successfully!\n"
            f"💰 Updated Balance: ₹{new_balance:,.2f}"
        )

    # ---------------- P2P TRANSFER ----------------
    if "send" in msg or "transfer" in msg:

        parts = msg.split()
        nums = [p for p in parts if p.isdigit()]

        if not nums:
            return "💡 Example: send 1000 to demo"

        amount = int(nums[0])
        receiver = parts[-1]

        if amount <= 0:
            return "❌ Enter a valid amount."

        receiver_user = get_user(receiver)

        if not receiver_user:
            return "❌ Receiver account not found."

        # 🔄 Reload fresh balance
        fresh_sender = get_user(username)
        fresh_balance = fresh_sender["balance"]

        if fresh_balance < amount:
            return "❌ Insufficient balance."

        # ✅ Deduct sender correctly
        new_sender_balance = fresh_balance - amount
        update_balance(username, new_sender_balance)

        # ✅ Add to receiver correctly
        fresh_receiver = get_user(receiver)
        new_receiver_balance = fresh_receiver["balance"] + amount
        update_balance(receiver, new_receiver_balance)

        # ✅ Add transaction
        add_transaction(
            category="Transfer",
            tx_type=f"Sent to {receiver}",
            amount=-amount
        )

        # 🔄 Sync session
        st.session_state.users[username]["bal"] = new_sender_balance

        return (
            f"✅ Transfer Successful!\n"
            f"➡️ Sent ₹{amount:,.2f} to {receiver}\n"
            f"💰 Your Balance: ₹{new_sender_balance:,.2f}"
        )

    # ---------------- DEFAULT ----------------
    return (
        "ℹ️ I can help with:\n"
        "• Check balance\n"
        "• Add money (add 5000)\n"
        "• P2P transfer (send 1000 to demo)\n"
        "• Card status\n"
        "• Loan / EMI"
    )
def ollama_reply(message):

    msg = message.lower()

    # 🔒 1️⃣ Force Offline for Transaction Keywords (from JSON safely)
    transaction_keywords = bank_ai.get("transaction_keywords", [])
    if any(word in msg for word in transaction_keywords):
        return offline_bank_reply(message)

    # 🔒 2️⃣ AI Toggle Check
    if not st.session_state.get("ai_enabled", True):
        return offline_bank_reply(message)

    # 🔒 3️⃣ Banking Intent Restriction
    finance_keywords = [
        "open", "close", "apply", "create",
        "bank", "account", "savings", "current",
        "money", "save", "deposit", "withdraw",
        "credit", "debit", "card", "loan", "emi",
        "interest", "budget", "finance", "investment"
    ]

    allowed = any(keyword in msg for keyword in finance_keywords)

    blocked_topics = bank_ai.get("ai_restrictions", {}).get("blocked_topics", [])
    blocked = any(word in msg for word in blocked_topics)

    if not allowed or blocked:
        return bank_ai.get("ai_restrictions", {}).get(
            "fallback_message",
            "⚠️ I can only assist with banking-related queries."
        )

    # 🔥 4️⃣ AI Streaming
    try:
        response_text = ""

        for chunk in ollama.chat(
            model="qwen2.5:1.5b",
            messages=[
                {"role": "system", "content": bank_ai.get("system_prompt", "")},
                {"role": "user", "content": message}
            ],
            stream=True
        ):
            if "message" in chunk and "content" in chunk["message"]:
                response_text += chunk["message"]["content"]

        return response_text.strip()

    except Exception as e:
        return "⚠️ AI service unavailable. Please try again later."
    
def generate_otp():
    return str(random.randint(100000, 999999))
def send_otp_notification(otp):
    try:
        notification.notify(
            title="NeoBank AI - OTP Verification",
            message=f"Your OTP is {otp}. Do not share it with anyone.",
            app_name="NeoBank AI",
            timeout=10
        )
    except Exception:
        print("Notification failed. OTP:", otp)
# ---------------- PAGE: LOGIN ----------------
def login_page():

    # ================= SESSION INITIALIZATION =================
    if "otp_time" not in st.session_state:
        st.session_state.otp_time = None

    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0

    if "show_register" not in st.session_state:
        st.session_state.show_register = False

    if "otp_sent" not in st.session_state:
        st.session_state.otp_sent = False

    _, col, _ = st.columns([1, 1.5, 1])

    with col:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.title("🏦 NeoBank AI")

        # ================= REGISTER PAGE =================
        if st.session_state.show_register:

            st.subheader("📝 Create New Account")

            full_name = st.text_input("Full Name")
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")

            if st.button("Register", use_container_width=True):

                if not full_name or not new_username or not new_password:
                    st.error("⚠ All fields are required")
                else:
                    success = register_user(
                        new_username,
                        new_password,
                        full_name
                    )

                    if success:
                        st.success("✅ Account created successfully")
                        st.session_state.show_register = False
                        st.rerun()
                    else:
                        st.error("❌ Username already exists")

            if st.button("⬅ Back to Login"):
                st.session_state.show_register = False
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
            return

        # ================= LOGIN STEP 1 =================
        if not st.session_state.otp_sent:

            u = st.text_input("Username")
            p = st.text_input("Password", type="password")

            if st.button("Login", use_container_width=True):

                if st.session_state.login_attempts >= 3:
                    st.error("❌ Too many failed attempts. Restart app.")
                    return

                db_user = authenticate_user(u, p)

                if db_user:

                    otp = generate_otp()

                    st.session_state.generated_otp = otp
                    st.session_state.temp_user = u
                    st.session_state.otp_sent = True
                    st.session_state.otp_time = datetime.now()

                    send_otp_notification(otp)

                    st.success("🔐 OTP sent successfully")
                    st.rerun()

                else:
                    st.session_state.login_attempts += 1
                    st.error("❌ Invalid username or password")

            if st.button("Open New Account", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()

        # ================= LOGIN STEP 2 (OTP) =================
        else:

            entered_otp = st.text_input("Enter OTP", max_chars=6)

            # OTP Expiry (2 Minutes)
            if st.session_state.otp_time:
                elapsed = (datetime.now() - st.session_state.otp_time).seconds
                if elapsed > 120:
                    st.error("⏰ OTP expired. Please login again.")
                    st.session_state.otp_sent = False
                    st.session_state.generated_otp = None
                    st.session_state.temp_user = None
                    st.session_state.otp_time = None
                    st.rerun()

            if st.button("Verify OTP", use_container_width=True):

                if entered_otp == st.session_state.generated_otp:

                    username = st.session_state.temp_user
                    db_user = get_user(username)

                    if not db_user:
                        st.error("❌ User not found.")
                        return

                    # Load session
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.transactions = get_transactions(username)

                    # Reset security states
                    st.session_state.otp_sent = False
                    st.session_state.generated_otp = None
                    st.session_state.temp_user = None
                    st.session_state.otp_time = None
                    st.session_state.login_attempts = 0

                    st.success("✅ Login successful")
                    st.rerun()

                else:
                    st.error("❌ Invalid OTP")

            if st.button("Resend OTP"):
                otp = generate_otp()
                st.session_state.generated_otp = otp
                st.session_state.otp_time = datetime.now()
                send_otp_notification(otp)
                st.info("📩 New OTP sent")

        st.markdown('</div>', unsafe_allow_html=True)

def generate_transaction_pdf(user, transactions_df):

    from Database.user_service import get_user

    # 🔄 Always fetch fresh user from DB
    db_user = get_user(user)

    if not db_user:
        return None

    file_name = f"transaction_history_{user}.pdf"

    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4

    # ================= HEADER =================
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 40, "NeoBank AI")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 65, "Transaction Statement")

    c.setFont("Helvetica", 10)
    c.drawString(40, height - 90, f"Account Holder: {db_user.get('full_name', 'User')}")
    c.drawString(40, height - 105, f"Account Number: {user.upper()}001")
    c.drawString(40, height - 120, f"Generated On: {datetime.now().strftime('%d-%m-%Y %H:%M')}")

    # Line separator
    c.line(40, height - 130, width - 40, height - 130)

    # ================= TABLE HEADER =================
    y = height - 150
    c.setFont("Helvetica-Bold", 10)

    c.drawString(40, y, "Date")
    c.drawString(150, y, "Category")
    c.drawString(260, y, "Type")
    c.drawRightString(width - 50, y, "Amount (₹)")

    y -= 15
    c.setFont("Helvetica", 10)

    # ================= TABLE DATA =================
    for _, row in transactions_df.iterrows():

        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 50

        date_val = str(row.get("Date", ""))
        category_val = str(row.get("Category", ""))
        type_val = str(row.get("Type", ""))
        amount_val = float(row.get("Amount", 0))

        c.drawString(40, y, date_val[:16])
        c.drawString(150, y, category_val[:15])
        c.drawString(260, y, type_val[:20])
        c.drawRightString(width - 50, y, f"{amount_val:,.2f}")

        y -= 15

    # ================= FOOTER =================
    c.line(40, y - 5, width - 40, y - 5)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y - 20, f"Current Balance: ₹{db_user.get('balance', 0):,.2f}")

    c.save()

    return file_name
# ---------------- PAGE: DASHBOARD ----------------
def dashboard_page():

    username = st.session_state.get("current_user")

    if not username:
        st.error("User not found.")
        return

    # 🔄 Load fresh DB data
    db_user = get_user(username)

    if not db_user:
        st.error("User not found in database.")
        return

    # 🔒 Ensure session user dict
    if "users" not in st.session_state:
        st.session_state.users = {}

    if username not in st.session_state.users:
        st.session_state.users[username] = {}

    st.session_state.users[username]["bal"] = db_user.get("balance", 0)
    st.session_state.users[username]["name"] = db_user.get("full_name", "User")

    user = st.session_state.users[username]

    st.title(f"Dashboard | {user['name']}")

    # ================= KPI CARDS =================
    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Account Balance", f"₹{db_user['balance']:,.2f}")
    k2.metric("Monthly Spending", "₹9,700", "-12%", delta_color="inverse")
    k3.metric("Credit Score", "785", "Excellent")
    k4.metric("Active Loans", "₹3,50,000")

    st.divider()

    # ================= PAYMENTS =================
    st.subheader("💸 Payments & Transfers")
    c1, c2 = st.columns(2)

    # -------- ADD MONEY --------
    with c1:
        st.markdown("### ➕ Add Money")

        with st.form("add_money_dashboard"):
            add_amt = st.number_input("Amount (₹)", min_value=1, step=500)
            add_btn = st.form_submit_button("Add Money")

            if add_btn:

                update_balance(username, add_amt)

                add_transaction(
                    category="Income",
                    tx_type="Cash Deposit",
                    amount=add_amt
                )

                st.success(f"✅ ₹{add_amt:,.2f} added successfully!")
                st.rerun()

    # -------- P2P TRANSFER --------
    with c2:
        st.markdown("### 🔁 P2P Transfer")

        with st.form("p2p_dashboard"):
            receiver = st.text_input("Receiver Username")
            send_amt = st.number_input("Amount to Send (₹)", min_value=1, step=500)
            send_btn = st.form_submit_button("Send Money")

            if send_btn:

                receiver_user = get_user(receiver)

                if not receiver_user:
                    st.error("❌ Receiver not found")

                else:
                    fresh_sender = get_user(username)
                    fresh_balance = fresh_sender["balance"]

                    if fresh_balance < send_amt:
                        st.error("❌ Insufficient balance")

                    else:
                        # Deduct sender
                        update_balance(username, -send_amt)

                        # Add to receiver
                        update_balance(receiver, send_amt)

                        add_transaction(
                            category="Transfer",
                            tx_type=f"Sent to {receiver}",
                            amount=-send_amt
                        )

                        st.success(f"✅ ₹{send_amt:,.2f} sent to {receiver}")
                        st.rerun()

    st.divider()

    # ================= SPENDING ANALYSIS =================
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.subheader("📊 Spending Analysis")

        df = get_transactions(username)

        if df is not None and not df.empty:

            spending_df = df[df["amount"] < 0].copy()

            if not spending_df.empty:
                spending_df["amount"] = spending_df["amount"].abs()

                fig = px.pie(
                    spending_df,
                    values="amount",
                    names="category",
                    hole=0.4
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Transaction History")
            st.dataframe(df, use_container_width=True)

        else:
            st.info("No transactions available.")

    # ================= CARD MANAGEMENT =================
    with col_right:
        st.subheader("💳 Card Management")

        if "cards" not in st.session_state:
            st.session_state.cards = {
                "debit": {
                    "active": True,
                    "num": "4532 •••• •••• 8892",
                    "expiry": "12/28"
                },
                "credit": {
                    "active": True,
                    "num": "5241 •••• •••• 1104",
                    "expiry": "05/29"
                }
            }

        # ---------- DEBIT ----------
        st.markdown(
            get_card_ui("debit", st.session_state.cards["debit"]),
            unsafe_allow_html=True
        )

        if st.session_state.cards["debit"]["active"]:
            if st.button("🔒 Block Debit Card", key="block_debit"):
                st.session_state.cards["debit"]["active"] = False
                st.rerun()
        else:
            if st.button("🔓 Unblock Debit Card", key="unblock_debit"):
                st.session_state.cards["debit"]["active"] = True
                st.rerun()

        st.divider()

        # ---------- CREDIT ----------
        st.markdown(
            get_card_ui("credit", st.session_state.cards["credit"]),
            unsafe_allow_html=True
        )

        if st.session_state.cards["credit"]["active"]:
            if st.button("🔒 Block Credit Card", key="block_credit"):
                st.session_state.cards["credit"]["active"] = False
                st.rerun()
        else:
            if st.button("🔓 Unblock Credit Card", key="unblock_credit"):
                st.session_state.cards["credit"]["active"] = True
                st.rerun()

    st.divider()

    # ================= LOAN ELIGIBILITY =================
    st.subheader("🏦 Loan Eligibility Calculator")

    col1, col2 = st.columns(2)

    with col1:
        requested_loan = st.number_input(
            "Requested Loan Amount (₹)",
            min_value=1000,
            step=5000
        )

    with col2:
        monthly_payment = st.number_input(
            "Your Monthly Payment Capacity (₹)",
            min_value=500,
            step=1000
        )

    tenure_years = st.slider("Loan Tenure (Years)", 1, 10, 3)

    if st.button("Check Loan Eligibility"):

        interest_rate = 0.10
        months = tenure_years * 12
        monthly_rate = interest_rate / 12

        emi = (
            requested_loan * monthly_rate *
            (1 + monthly_rate) ** months
        ) / (
            ((1 + monthly_rate) ** months) - 1
        )

        st.markdown("### 📊 Loan Result")
        st.write(f"Estimated EMI: ₹{emi:,.2f}")
        st.write(f"Tenure: {months} months")
        st.write("Interest Rate: 10% per annum")

        if monthly_payment >= emi:
            st.success("✅ You are eligible for this loan amount!")
        else:
            approx_loan = monthly_payment * months
            st.error("❌ Not eligible for requested amount.")
            st.warning(f"You may qualify for approx ₹{approx_loan:,.0f}")
# ---------------- PAGE: AI CHAT ----------------
def chat_page(): 
    st.title("🤖 AI Banking Assistant")

    username = st.session_state.current_user

    # 🔄 Initialize chat session if not exists
    if not st.session_state.current_chat:
        cid = f"Chat {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.chat_history[cid] = []
        st.session_state.current_chat = cid

    # 🔄 Load chat history from MongoDB (only once per session)
    if "chat_loaded" not in st.session_state:
        db_chats = get_chat_history(username)

        for chat in db_chats:
            role = chat["role"]
            msg = chat["message"]

            if st.session_state.current_chat not in st.session_state.chat_history:
                st.session_state.chat_history[st.session_state.current_chat] = []

            st.session_state.chat_history[st.session_state.current_chat].append((role, msg))

        st.session_state.chat_loaded = True

    # ---------------- DISPLAY CHAT HISTORY ----------------
    for role, msg in st.session_state.chat_history[st.session_state.current_chat]:
        st.markdown(
            f'<div class="{"user-bubble" if role=="user" else "bot-bubble"}">{msg}</div>',
            unsafe_allow_html=True
        )

    # ---------------- QUICK ACTIONS ----------------
    st.write("### Quick Actions")

    q1, q2, q3, q4 = st.columns(4)

    if q1.button("Check Balance"):
        handle_chat("What is my current balance?")

    if q2.button("Security Check"):
        handle_chat("Are my cards blocked?")

    if q3.button("Spending Tips"):
        handle_chat("How can I save money this month?")

    if q4.button("💳 Debit Card Status"):
        handle_chat("What is my debit card status?")

    q5, q6, q7 = st.columns(3)

    if q5.button("💳 Credit Card Status"):
        handle_chat("What is my credit card status?")

    if q6.button("📆 EMI Details"):
        handle_chat("Tell me my EMI details")

    if q7.button("🏦 Loan Info"):
        handle_chat("Tell me my loan balance")

    # ---------------- CHAT INPUT ----------------
    prompt = st.chat_input("Ask me about blocking cards, interest rates, or your balance...")

    if prompt:
        handle_chat(prompt)

def handle_chat(txt):

    username = st.session_state.current_user

    # Auto create chat session
    if not st.session_state.current_chat:
        cid = f"Chat {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.chat_history[cid] = []
        st.session_state.current_chat = cid

    # ================= SAVE USER MESSAGE =================
    st.session_state.chat_history[st.session_state.current_chat].append(("user", txt))
    save_chat(username, "user", txt)

    # ================= DECIDE REPLY =================
    lower_txt = txt.lower()

    try:
        # Banking keywords → offline logic
        if any(w in lower_txt for w in ["add", "deposit", "send", "transfer", "balance"]):
            reply = offline_bank_reply(txt)

        else:
            if st.session_state.ai_enabled:
                with st.spinner("🤖 AI is thinking..."):
                    reply = ollama_reply(txt)
            else:
                reply = offline_bank_reply(txt)

    except Exception as e:
        reply = "⚠️ Something went wrong while processing your request."
        print("Chat Error:", e)

    # ================= TYPING EFFECT =================
    if st.session_state.ai_enabled:
        placeholder = st.empty()
        typed_text = ""

        for char in reply:
            typed_text += char
            placeholder.markdown(
                f'<div class="bot-bubble">{typed_text}</div>',
                unsafe_allow_html=True
            )
            time.sleep(0.01)

        placeholder.empty()

    # ================= SAVE BOT REPLY =================
    st.session_state.chat_history[st.session_state.current_chat].append(("bot", reply))
    save_chat(username, "bot", reply)

    st.rerun()

# ---------------- SIDEBAR ----------------
def sidebar(): 
    with st.sidebar:

        username = st.session_state.current_user

        # 🔄 Always load fresh user data from DB
        db_user = get_user(username)

        # Sync session
        # Ensure users dictionary exists
        if "users" not in st.session_state:
            st.session_state.users = {}
        # Ensure user key exists
        if username not in st.session_state.users:
            st.session_state.users[username] = {}
        st.session_state.users[username]["name"] = db_user.get("full_name", "User")
        st.session_state.users[username]["bal"] = db_user["balance"]

        user_data = st.session_state.users[username]

        # ---------------- PROFILE CARD ----------------
        st.markdown(f"""
        <div class="profile-box">
            <h3>🏦 NeoBank AI</h3>
            <p style="font-size:13px;opacity:0.7;">
                {user_data['name']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ---------------- USER INFO ----------------
        st.markdown("## 👤 User Profile")
        st.write(f"**Name:** {user_data['name']}")
        st.write("**Tier:** Gold Member")

        # ---------------- ACCOUNT INFORMATION ----------------
        st.markdown("### 🏦 Account Information")

        st.markdown(f"""
        <div style="
            background:linear-gradient(145deg,#0f172a,#111827);
            padding:15px;
            border-radius:12px;
            border:1px solid #1f2937;
            margin-bottom:15px;
            font-size:13px;
        ">
            <p><strong>Account Number:</strong><br>{username.upper()}001</p>
            <p><strong>Balance:</strong><br>₹{user_data['bal']:,.2f}</p>
            <p><strong>Account Type:</strong><br>Savings</p>
            <p><strong>Credit Score:</strong><br>785</p>
            <p><strong>Debit Card:</strong> {"Active ✅" if st.session_state.cards["debit"]["active"] else "Blocked ❌"}</p>
            <p><strong>Credit Card:</strong> {"Active ✅" if st.session_state.cards["credit"]["active"] else "Blocked ❌"}</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ---------------- NAVIGATION ----------------
        st.session_state.page = st.radio(
            "Navigation",
            ["Dashboard", "AI Assistant"]
        )

        st.session_state.ai_enabled = st.toggle(
            "Enable AI Intelligence",
            value=st.session_state.ai_enabled
        )

        st.divider()

        # ---------------- CHAT HISTORY ----------------
        st.markdown("### 🕒 History")

        if st.button("➕ New Chat Session", use_container_width=True):
            cid = f"Chat {datetime.now().strftime('%H:%M:%S')}"
            st.session_state.chat_history[cid] = []
            st.session_state.current_chat = cid
            st.rerun()

        for cid in list(st.session_state.chat_history.keys())[::-1]:
            c_sel, c_del = st.columns([4, 1])

            if c_sel.button(f"💬 {cid}", key=f"s_{cid}", use_container_width=True):
                st.session_state.current_chat = cid
                st.rerun()

            if c_del.button("🗑", key=f"d_{cid}"):

                # 🔥 Remove from MongoDB also
                delete_chat_session(username)

                del st.session_state.chat_history[cid]

                if st.session_state.current_chat == cid:
                    st.session_state.current_chat = None

                st.rerun()

        st.divider()

        # ---------------- LOGOUT ----------------
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# ---------------- MAIN APP ----------------
if not st.session_state.logged_in:
    login_page()
else:
    sidebar()
    if st.session_state.page == "Dashboard": dashboard_page()
    else: chat_page()