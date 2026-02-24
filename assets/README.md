# 🏦 NeoBank AI – Intelligent Digital Banking Assistant

NeoBank AI is a **smart digital banking web application** built using **Streamlit** and **Ollama (Local LLMs)**.  
It combines **rule-based banking operations** with **AI-powered assistance**, optimized for **offline and low-resource PCs**.

---

## 🚀 Features

### 🔐 User & Account Management
- Secure login & registration
- User profile with account details
- Savings account simulation

### 💰 Banking Operations (Offline & Instant)
- Check account balance
- Add money to account
- P2P money transfer
- Debit & credit card status
- Loan & EMI information

### 💳 Card Management
- Debit card block / unblock
- Credit card block / unblock
- Real-time status update

### 📊 Dashboard & Analytics
- Account KPIs
- Spending analysis (charts)
- Recent transaction history

### 🤖 AI Banking Assistant
- AI-powered financial tips & FAQs
- Streaming (typing-style) responses
- AI Enable / Disable toggle
- Automatic fallback to offline logic
- Optimized for fast response on CPU

---

## 🧠 AI Design (Hybrid Approach)

| Task Type | Processing Mode |
|---------|----------------|
| Balance / Transfers | Rule-based (Offline) |
| Card Actions | Rule-based (Offline) |
| Financial Advice | AI (LLM) |
| FAQs & Guidance | AI (LLM) |

This ensures:
- ⚡ Instant response for critical banking actions  
- 🤖 AI used only where required  
- 🔐 Safe & predictable behavior  

---

## 🧩 Tech Stack

- **Frontend:** Streamlit
- **Backend Logic:** Python
- **AI Engine:** Ollama (Local LLM)
- **Charts:** Plotly
- **Data Handling:** Pandas
- **Models Supported:**
  - `qwen2.5:1.5b` (Recommended – Fast)
  - `phi3-fast`
  - `phi-3-mini`
  - `tinyllama`

---

## 🖥️ System Requirements

**Minimum**
- CPU: Intel i3 / Ryzen 3
- RAM: 8 GB
- OS: Windows / Linux / macOS

**Recommended**
- CPU: Intel i5 / Ryzen 5
- RAM: 16 GB
- SSD storage

> ⚠️ GPU is NOT required

---

## ⚡ Recommended AI Model (Fastest)

```text
qwen2.5:1.5b