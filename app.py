import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ollama
import time

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
    active_status = "ACTIVE" if info['active'] else "BLOCKED"
    block_style = "" if info['active'] else "card-blocked"
    bg = "linear-gradient(135deg, #1e40af, #3b82f6)" if card_type == 'debit' else "linear-gradient(135deg, #581c87, #a855f7)"
    
    return f"""
    <div class="bank-card {block_style}" style="background: {bg};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <span style="font-weight: bold; font-size: 14px;">{card_type.upper()} PLATINUM</span>
            <span style="background: rgba(0,0,0,0.4); font-size: 9px; padding: 2px 6px; border-radius: 4px;">{active_status}</span>
        </div>
        <div style="margin-top: 25px; font-size: 18px; letter-spacing: 2px;">{info['num']}</div>
        <div style="margin-top: 25px; display: flex; justify-content: space-between;">
            <div><div class="card-label">Card Holder</div><div style="font-size: 12px;">{st.session_state.users[st.session_state.current_user]['name']}</div></div>
            <div><div class="card-label">Expires</div><div style="font-size: 12px;">{info['expiry']}</div></div>
        </div>
    </div>
    """
def offline_bank_reply(message):
    msg = message.lower()
    user = st.session_state.users.get(st.session_state.current_user, {})

    # ---------------- BALANCE ----------------
    if "balance" in msg:
        return f"💰 Your balance is ₹{user.get('bal',0):,.2f}"

    # ---------------- CARD STATUS ----------------
    if "card" in msg:
        debit = "Active ✅" if st.session_state.cards["debit"]["active"] else "Blocked ❌"
        credit = "Active ✅" if st.session_state.cards["credit"]["active"] else "Blocked ❌"
        return f"💳 Debit Card: {debit}\n💳 Credit Card: {credit}"

    # ---------------- LOAN / EMI ----------------
    if "loan" in msg or "emi" in msg:
        return "🏦 EMI: ₹12,500/month | Loan Outstanding: ₹3,50,000"

    # ================= ADD MONEY (FIXED) =================
    if "add" in msg or "deposit" in msg:
        amount = "".join(ch for ch in msg if ch.isdigit())

        if amount:
            amount = int(amount)
            if amount <= 0:
                return "❌ Enter a valid amount."

            user["bal"] += amount
            return (
                f"✅ ₹{amount:,.2f} added successfully!\n"
                f"💰 Updated Balance: ₹{user['bal']:,.2f}"
            )
        else:
            return "💡 Example: add 5000"

    # ================= P2P TRANSFER =================
    if "send" in msg or "transfer" in msg:
        parts = msg.split()
        nums = [p for p in parts if p.isdigit()]

        if not nums:
            return "💡 Example: send 1000 to demo"

        amount = int(nums[0])
        receiver = parts[-1]

        if receiver not in st.session_state.users:
            return "❌ Receiver account not found."

        if user.get("bal", 0) < amount:
            return "❌ Insufficient balance."

        user["bal"] -= amount
        st.session_state.users[receiver]["bal"] += amount

        return (
            f"✅ Transfer Successful!\n"
            f"➡️ Sent ₹{amount:,.2f} to {receiver}\n"
            f"💰 Your Balance: ₹{user['bal']:,.2f}"
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

    # 🔥 FORCE OFFLINE FOR TRANSACTIONS
    transaction_words = ["add", "deposit", "send", "transfer", "balance"]

    if any(word in msg for word in transaction_words):
        return offline_bank_reply(message)

    # AI disabled
    if not st.session_state.ai_enabled:
        return offline_bank_reply(message)

    try:
        response_text = ""
        placeholder = st.empty()

        # 🔥 STREAMING RESPONSE (FAST FEEL)
        for chunk in ollama.chat(
            model="phi3-fast",   # ⬅ use fast model
            messages=[
                {"role": "system", "content": "Banking assistant. Short answers."},
                {"role": "user", "content": message}
            ],
            stream=True
        ):
            token = chunk["message"]["content"]
            response_text += token

            # Live typing effect
            placeholder.markdown(
                f'<div class="bot-bubble">{response_text}</div>',
                unsafe_allow_html=True
            )

        return response_text

    except Exception:
        return offline_bank_reply(message)
# ---------------- PAGE: LOGIN ----------------
def login_page():
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">🏦 NeoBank AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Secure • Smart • AI Powered Banking</div>', unsafe_allow_html=True)
        st.title("🏦 NeoBank AI")
        
        if not st.session_state.show_register:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                if u in st.session_state.users and st.session_state.users[u]['pass'] == p:
                    st.session_state.logged_in = True
                    st.session_state.current_user = u
                    st.rerun()
                else: st.error("Invalid credentials")
            st.button("Open New Account", on_click=lambda: st.session_state.update({"show_register": True}))
        else:
            new_u = st.text_input("New Username")
            new_n = st.text_input("Full Name")
            new_p = st.text_input("New Password", type="password")
            if st.button("Register & Deposit ₹5000", use_container_width=True):
                st.session_state.users[new_u] = {"pass": new_p, "name": new_n, "bal": 5000.0}
                st.session_state.show_register = False
                st.success("Account Created!")
                time.sleep(1); st.rerun()
            st.button("Back to Login", on_click=lambda: st.session_state.update({"show_register": False}))
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- PAGE: DASHBOARD ----------------
def dashboard_page():
    user = st.session_state.users[st.session_state.current_user]
    st.title(f"Dashboard | {user['name']}")
    
    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Account Balance", f"₹{user['bal']:,.2f}", "+₹2,400")
    k2.metric("Monthly Spending", "₹9,700", "-12%", delta_color="inverse")
    k3.metric("Credit Score", "785", "Excellent")
    k4.metric("Active Loans", "₹3,50,000")

    st.divider()

    # ===================== ADDED: ADD MONEY & P2P =====================
    st.subheader("💸 Payments & Transfers")

    c1, c2 = st.columns(2)

    # -------- ADD MONEY BLOCK --------
    with c1:
        st.markdown("### ➕ Add Money")
        with st.form("add_money_dashboard"):
            add_amt = st.number_input("Amount (₹)", min_value=1, step=500)
            add_btn = st.form_submit_button("Add Money")

            if add_btn:
                user["bal"] += add_amt
                st.success(f"✅ ₹{add_amt:,.2f} added successfully!")
                st.rerun()

    # -------- P2P TRANSFER BLOCK --------
    with c2:
        st.markdown("### 🔁 P2P Transfer")
        with st.form("p2p_dashboard"):
            receiver = st.text_input("Receiver Username")
            send_amt = st.number_input("Amount to Send (₹)", min_value=1, step=500)
            send_btn = st.form_submit_button("Send Money")

            if send_btn:
                if receiver not in st.session_state.users:
                    st.error("❌ Receiver not found")
                elif user["bal"] < send_amt:
                    st.error("❌ Insufficient balance")
                else:
                    user["bal"] -= send_amt
                    st.session_state.users[receiver]["bal"] += send_amt
                    st.success(f"✅ ₹{send_amt:,.2f} sent to {receiver}")
                    st.rerun()

    st.divider()
    # ===================== END ADDITION =====================

    # Column Layout
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.subheader("📊 Spending Analysis")
        df = st.session_state.transactions
        spending_df = df[df['Amount'] < 0].copy()
        spending_df['Amount'] = spending_df['Amount'].abs()

        fig = px.pie(
            spending_df,
            values='Amount',
            names='Category',
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu,
            template="plotly_dark"
        )
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Recent Activity")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("💳 Card Management")
        
        # Debit Card
        st.markdown(get_card_ui("debit", st.session_state.cards["debit"]), unsafe_allow_html=True)
        d_label = "Unblock Debit Card" if not st.session_state.cards["debit"]["active"] else "Block Debit Card"
        if st.button(d_label, use_container_width=True):
            st.session_state.cards["debit"]["active"] = not st.session_state.cards["debit"]["active"]
            st.rerun()

        # Credit Card
        st.markdown(get_card_ui("credit", st.session_state.cards["credit"]), unsafe_allow_html=True)
        c_label = "Unblock Credit Card" if not st.session_state.cards["credit"]["active"] else "Block Credit Card"
        if st.button(c_label, use_container_width=True):
            st.session_state.cards["credit"]["active"] = not st.session_state.cards["credit"]["active"]
            st.rerun()

    st.divider()
    
    # Loan Eligibility Feature
    with st.expander("🚀 Check Loan Eligibility"):
        st.write("Instant AI Assessment based on your profile.")
        l1, l2 = st.columns(2)
        income = l1.number_input("Monthly Income (₹)", value=60000)
        existing_emi = l2.number_input("Existing EMIs (₹)", value=5000)
        if st.button("Calculate Eligibility"):
            score = (income - existing_emi) * 0.4 * 12 * 3
            st.success(f"You are eligible for a loan up to: ₹{score:,.0f}")

# ---------------- PAGE: AI CHAT ----------------
def chat_page(): 
    st.title("🤖 AI Banking Assistant")
    if st.session_state.current_chat not in st.session_state.chat_history:
        st.info("Chat session not found. Please start a new chat.")
        return
    
    if not st.session_state.current_chat:
        st.info("Start a new session or select one from the sidebar history.")
        return

    # ---------------- DISPLAY CHAT HISTORY ----------------
    for role, msg in st.session_state.chat_history[st.session_state.current_chat]:
        st.markdown(
            f'<div class="{"user-bubble" if role=="user" else "bot-bubble"}">{msg}</div>',
            unsafe_allow_html=True
        )

    # ---------------- QUICK ACTIONS ----------------
    st.write("### Quick Actions")

    # -------- First Row (4 buttons) --------
    q1, q2, q3, q4 = st.columns(4)

    if q1.button("Check Balance"):
        handle_chat("What is my current balance?")

    if q2.button("Security Check"):
        handle_chat("Are my cards blocked?")

    if q3.button("Spending Tips"):
        handle_chat("How can I save money this month?")

    if q4.button("💳 Debit Card Status"):
        handle_chat("What is my debit card status?")

    # -------- Second Row (3 buttons) --------
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

    # Auto create chat
    if not st.session_state.current_chat:
        cid = f"Chat {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.chat_history[cid] = []
        st.session_state.current_chat = cid

    # Add user message
    st.session_state.chat_history[st.session_state.current_chat].append(("user", txt))

    # Decide reply
    if any(w in txt.lower() for w in ["add", "deposit", "send", "transfer", "balance"]):
        reply = offline_bank_reply(txt)
    else:
        if st.session_state.ai_enabled:
            with st.spinner("🤖 AI is thinking..."):
                reply = ollama_reply(txt)
        else:
            reply = offline_bank_reply(txt)

    # Typing effect
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

    # Save final reply
    st.session_state.chat_history[st.session_state.current_chat].append(("bot", reply))

    st.rerun()

# ---------------- SIDEBAR ----------------
def sidebar(): 
    with st.sidebar:

        # ---------------- PROFILE CARD ----------------
        st.markdown(f"""
        <div class="profile-box">
            <h3>🏦 NeoBank AI</h3>
            <p style="font-size:13px;opacity:0.7;">
                {st.session_state.users[st.session_state.current_user]['name']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ---------------- USER INFO ----------------
        st.markdown("## 👤 User Profile")
        st.write(f"**Name:** {st.session_state.users[st.session_state.current_user]['name']}")
        st.write("**Tier:** Gold Member")

        # ---------------- ACCOUNT INFORMATION ----------------
        st.markdown("### 🏦 Account Information")

        user_data = st.session_state.users[st.session_state.current_user]

        st.markdown(f"""
        <div style="
            background:linear-gradient(145deg,#0f172a,#111827);
            padding:15px;
            border-radius:12px;
            border:1px solid #1f2937;
            margin-bottom:15px;
            font-size:13px;
        ">
            <p><strong>Account Number:</strong><br>{st.session_state.current_user.upper()}001</p>
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