# OmniFinance: Autonomous Banking & Digital Wallet Sandbox

OmniFinance is a multi-agent digital banking sandbox leveraging Google's Agent Development Kit (ADK) routing principles and Model Context Protocol (MCP) schemas.

## Core Capabilities
1. **Digital Wallet Simulator**: Manages virtual balances, accounts, and a live ledger database using SQLite.
2. **Autonomous Expense Tracker (Agent B)**: Extracts transaction details (`amount`, `merchant`, `category`, `timestamp`) from raw user text or voice requests.
3. **AI Fraud Detection Agent (Agent C)**: Evaluates composite risk based on transaction parameters. If the risk exceeds 75%, it triggers a Human-in-the-Loop (HITL) pause, locking the transaction until approved.
4. **Financial Literacy Coach (Agent D)**: Explains budgeting, diversification, inflation, and compound interest using inline analogical expansions.
5. **Central Orchestrator (Agent A)**: Dynamically routes incoming queries to the target sub-agents and coordinates tool executions.

---

## 📁 File Structure
```
F:\bank-ai\
├── main.py                 # FastAPI Application (Router, Endpoints, MCP Tool execution)
├── config.py               # Configuration & Env variable loader
├── requirements.txt        # Package dependencies
├── omnifinance.db          # SQLite Database (generated on startup)
├── test_sandbox.py         # End-to-end sandbox verification script
├── implement.md            # Next.js UI migration plan
│
├── database/
│   ├── __init__.py
│   └── db.py               # SQLite database access (atomic ledger logic, HITL state)
│
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py     # Central Orchestrator routing logic
│   ├── expense_tracker.py  # Expense tracker agent (with rule-based & LLM parsers)
│   ├── fraud_detector.py   # Fraud evaluator agent (risk score calculator)
│   └── literacy_coach.py   # Literacy coach (grounded references & inline expansions)
│
└── frontend/               # Next.js Frontend Dashboard Project
    ├── package.json        # Dependencies (React, Next.js, TypeScript)
    ├── next.config.ts      # Next.js configuration (static export setup)
    ├── public/             # Static assets (images, fonts, etc.)
    └── src/
        └── app/
            ├── globals.css # Premium dark theme stylesheet (custom properties, animations)
            ├── layout.tsx  # Dashboard layout metadata and FontAwesome CDN
            └── page.tsx    # Dashboard core view & React states
```

## 🎨 UI & Frontend Dashboard
The user interface is built as a highly responsive Single Page Application (SPA) using **Next.js (React) and TypeScript**. The UI utilizes a premium glassmorphic dark theme and features:
* **Real-time telemetry** of wallet balance and sandbox status metrics.
* **Interactive Chat Sandbox** to enter transactions or ask financial literacy questions.
* **Live Ledger Table** displaying transactions with color-coded risk indicators.
* **Human-in-the-Loop (HITL)** triggers enabling one-click approval/rejection of high-risk transactions.

---

## 🚀 Setup & Execution

### 1. Installation
Ensure you are running Python 3.10+ and Node.js 18+.

**Python Backend Dependencies:**
```bash
pip install -r requirements.txt
```

**Frontend Dependencies:**
```bash
cd frontend
npm install
cd ..
```

### 2. Run the Verification Simulation
Execute the local simulation script to test all agents, ledger updates, and fraud hooks automatically:
```bash
python test_sandbox.py
```

### 3. Build & Run the Web Application

**Option A: Compiled Production Sandbox Mode (Unified)**
First, compile the static Next.js build:
```bash
cd frontend
npm run build
cd ..
```
Then launch the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```
Open your browser and navigate to `http://127.0.0.1:8000` to view the unified Next.js dashboard UI served directly by FastAPI. Navigating to `http://127.0.0.1:8000/docs` displays the Swagger API docs.

**Option B: Separate Frontend & Backend Development Mode**
Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```
In a separate terminal, start the Next.js dev server:
```bash
cd frontend
npm run dev
```
Open `http://localhost:3000` to view the Next.js app in development mode, which automatically communicates with the FastAPI backend on port 8000 via CORS.

---

## ⚡ API Endpoints

### 💬 Orchestrator Chat (`POST /chat`)
Submit general chat queries, expenses, or financial questions.
* **Payload**:
  ```json
  {
    "prompt": "Spent $45 on pizza with friends last night",
    "session_id": "optional_session_uuid"
  }
  ```

### 🔓 Human-In-The-Loop Approval (`POST /transactions/approve`)
Resumes transaction execution paused by the Fraud Detection agent.
* **Payload**:
  ```json
  {
    "transaction_id": "tx_uuid_here",
    "approve": true
  }
  ```

### 🔌 MCP Tool Executions (`POST /tools/execute`)
Exposes direct tool execution for external orchestrators.
* **Payload**:
  ```json
  {
    "tool_name": "evaluate_fraud_risk",
    "arguments": {
      "amount": 5200.0,
      "location": "Suspicious Location",
      "velocity_mins": 2
    }
  }
  ```
* **Supported Tools**:
  * `log_transaction`
  * `evaluate_fraud_risk`
  * `fetch_financial_knowledge_base`


