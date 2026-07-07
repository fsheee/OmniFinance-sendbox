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
├── backend/                # FastAPI Backend Application
│   ├── main.py             # FastAPI Application (Router, Endpoints, MCP Tool execution)
│   ├── config.py           # Configuration & Env variable loader
│   ├── requirements.txt    # Package dependencies
│   ├── Dockerfile          # Container build instructions
│   ├── omnifinance.db      # SQLite Database (generated on startup)
│   ├── test_sandbox.py     # End-to-end sandbox verification script
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # Central Orchestrator routing logic
│   │   ├── expense_tracker.py  # Expense tracker agent (with rule-based & LLM parsers)
│   │   ├── fraud_detector.py   # Fraud evaluator agent (risk score calculator)
│   │   └── literacy_coach.py   # Literacy coach (grounded references & inline expansions)
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py               # SQLite database access (atomic ledger logic, HITL state)
│   │   └── vector_store.py     # ChromaDB vector store for semantic search
│   │
│   └── tests/
│       └── test_fraud_detector.py
│
├── frontend/               # Next.js Frontend Dashboard Project
│   ├── package.json        # Dependencies (React, Next.js, TypeScript)
│   ├── next.config.ts      # Next.js configuration (static export setup)
│   ├── public/             # Static assets (images, fonts, etc.)
│   └── src/
│       └── app/
│           ├── globals.css # Premium dark theme stylesheet (custom properties, animations)
│           ├── layout.tsx  # Dashboard layout metadata and FontAwesome CDN
│           └── page.tsx    # Dashboard core view & React states
│
├── tests/                  # Test suite
└── README.md
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

---

## 🤖 Agent Skills Registry

OmniFinance implements **Agent Skills** as a formal, discoverable system for exposing reusable agent capabilities. This enables:
- **Skill Discovery**: External orchestrators can query available skills
- **Tool Interoperability**: Standardized input/output contracts for skill invocation
- **Dependency Tracking**: Skills declare dependencies and chaining relationships
- **Performance Metrics**: Usage statistics and success rates per skill

### Available Agent Skills

The project exposes **3 core reusable agent skills**:

1. **Expense Tracker Skills** (from `expense_tracker.py` agent)
   - `parse_query`: Extract transaction details from natural language
   - `log_transaction`: Record transaction to ledger with validation

2. **Fraud Detector Skill** (from `fraud_detector.py` agent)
   - `evaluate_fraud_risk`: Calculate composite risk score (amount, location, velocity)

3. **Literacy Coach Skill** (from `literacy_coach.py` agent)
   - `answer_question`: Retrieve financial knowledge from ChromaDB and explain concepts

### Skill Discovery & Invocation

Skills can be discovered and invoked through standardized endpoints (planned for v2):
- Each skill has formal input/output schemas (JSON Schema format)
- Skills declare dependencies and what they can chain to
- Performance metrics track success rate, latency, and usage count

---

## 🧪 API Testing & Documentation

### Interactive API Documentation

FastAPI automatically generates interactive API documentation. After starting the server:

**Swagger UI** (Recommended):
```
http://127.0.0.1:8000/docs
```
- Browse all available endpoints
- Execute test requests directly from your browser
- View request/response schemas
- Test with example payloads

**ReDoc Alternative**:
```
http://127.0.0.1:8000/redoc
```
- Alternative API documentation viewer

### Complete Endpoint List

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/telemetry` | Get sandbox status, wallet balance, transaction summary |
| `GET` | `/knowledge/search` | Semantic search over financial literacy knowledge base |
| `POST` | `/chat` | Main orchestrator - route queries to appropriate agents |
| `POST` | `/transactions/approve` | Human-in-the-Loop approval/rejection of high-risk transactions |
| `POST` | `/tools/execute` | Direct tool execution for external orchestrators |
| `POST` | `/reset` | Reset sandbox to initial state ($5000 balance, cleared ledger) |
| `GET` | `/docs` | Swagger interactive API documentation |
| `GET` | `/redoc` | ReDoc alternative API documentation |

### Example Test Workflow

1. **Start the server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

2. **Open Swagger UI**:
   ```
   http://127.0.0.1:8000/docs
   ```

3. **Test a transaction** (POST `/chat`):
   ```json
   {
     "prompt": "Spent $85 at Starbucks yesterday morning",
     "session_id": "test_session_1"
   }
   ```

4. **Check wallet status** (GET `/api/telemetry`):
   - View updated balance and transaction count

5. **Search knowledge base** (GET `/knowledge/search`):
   ```
   ?query=compound%20interest&n_results=5
   ```

---

## API Authentication

Protected endpoints require API key in header:
```
X-API-Key: omnifinance-secret-key
```

## Quick Test
[Dashboard:](https://omnifinance-ten.vercel.app/) <br>
[API Docs:](https://afsheenkhi-omnifinance-api.hf.space/docs)


---

## 📊 Project Overview

**OmniFinance** is an enterprise-grade multi-agent banking sandbox implementing:

- **Agent-Oriented Architecture**: Follows Google's Agent Development Kit (ADK) patterns for distributed autonomous agents
- **Intelligent Routing**: Central orchestrator intelligently routes queries to specialized sub-agents
- **Financial Domain Expertise**: Agents specialize in expense tracking, fraud detection, and financial literacy
- **Human-in-the-Loop (HITL)**: Risk-triggered pause-and-approve workflow for high-risk transactions
- **Model Context Protocol (MCP)**: Standardized schemas for tool execution and agent interoperability
- **Vector Database**: ChromaDB integration for semantic search over financial knowledge
- **Production-Ready**: Atomic transactions, audit logging, structured error handling

### Key Features

✅ Real-time fraud detection with configurable risk thresholds  
✅ Semantic search over financial knowledge base  
✅ Transaction ledger with color-coded risk indicators  
✅ Dashboard telemetry for wallet monitoring  
✅ Extensible agent framework for adding new capabilities  
✅ Interactive API documentation with Swagger UI  


