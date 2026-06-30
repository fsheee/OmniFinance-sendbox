# OmniFinance Sandbox: Engineering Architecture & Build Plan

OmniFinance is an autonomous digital banking sandbox built with **FastAPI**, **Google ADK** (Agent Development Kit) routing principles, and **SQLite** (or Firestore). It simulates digital wallet operations, parses unstructured expenses, detects fraud anomalies using behavioral metrics, and coaches users on financial literacy using inline explanations.

---

## 📁 Project Structure & File Map

* **FastAPI Entrypoint:** [main.py](file:///F:/bank-ai/main.py) — Configures FastAPI endpoints, maps tool schemas, and exposes the Model Context Protocol (MCP) bridge.
* **Environment Configurations:** [config.py](file:///F:/bank-ai/config.py) — Handles global settings.
* **Project Dependencies:** [requirements.txt](file:///F:/bank-ai/requirements.txt) — Declares external requirements.
* **Local SQLite Interface:** [db.py](file:///F:/bank-ai/database/db.py) — Handles atomic balance deductions, transaction logging, and state storage.
* **Agent A (Central Orchestrator):** [orchestrator.py](file:///F:/bank-ai/agents/orchestrator.py) — Directs input prompts to specialized sub-agents and processes tool routing.
* **Agent B (Autonomous Expense Tracker):** [expense_tracker.py](file:///F:/bank-ai/agents/expense_tracker.py) — Extracts transaction schemas from natural text.
* **Agent C (AI Fraud Detection Agent):** [fraud_detector.py](file:///F:/bank-ai/agents/fraud_detector.py) — Computes fraud scores and manages HITL pauses.
* **Agent D (Financial Literacy Coach):** [literacy_coach.py](file:///F:/bank-ai/agents/literacy_coach.py) — Grounded knowledge matching and inline jargon expansion.
* **Test Simulation Harness:** [test_sandbox.py](file:///F:/bank-ai/test_sandbox.py) — Validation test running the complete multi-agent sandbox sequence.

---

## 🖼️ Visualized System Architecture

![Visualized System Architecture Flowchart](C:/Users/Kashif/.gemini/antigravity-cli/brain/17c69ba3-8647-433b-b23f-0933ed79f3fa/omnifinance_architecture_chart_1782420516730.jpg)

---

## 📊 System Execution Flowchart

```mermaid
flowchart TD
    Start([User Input Prompt]) --> AgentA{Agent A: Central Orchestrator}
    
    %% Intent Classification
    AgentA -->|Classifies as EXPENSE| AgentB[Agent B: Expense Tracker]

    AgentA -->|Classifies as LITERACY| AgentD[Agent D: Financial Coach]
    AgentA -->|Classifies as WALLET| DirectWallet[Direct Database Query]
    AgentA -->|Classifies as FRAUD| AgentC_Direct[Agent C: Fraud Risk Query]

    %% Agent B: Expense Flow
    AgentB -->|1. Parse Natural Text| ParseText[Extract: Amount, Merchant, Category, Timestamp]
    ParseText -->|2. Route to Fraud Checks| AgentC[Agent C: Fraud Detection Agent]
    AgentC -->|3. Evaluate Metrics| EvalFraud[Calculate Risk: Amount Risk + Velocity Risk + Location Risk]
    
    EvalFraud --> Decision{Is Risk Score > 75%?}
    
    %% Risk Decisions
    Decision -->|Yes| HitlPause[Log Transaction as 'PENDING_HITL']
    HitlPause --> ReturnPause[Return: 'PAUSED_WAITING_FOR_HITL'<br>Balance remains unchanged]
    ReturnPause --> UserAction([User calls /transactions/approve])
    UserAction --> Approve{Approved?}
    Approve -->|Yes| DB_Approve[Update Transaction to 'APPROVED']
    DB_Approve --> DeductBalance[Deduct Amount from Wallet Balance]
    Approve -->|No| DB_Reject[Update Transaction to 'REJECTED']
    
    Decision -->|No| DbCommit[Log Transaction as 'COMPLETED']
    DbCommit --> DeductBalance
    DeductBalance --> EndExpense([Done: Transaction Finalized])
    DB_Reject --> EndExpense

    %% Agent D: Literacy Flow
    AgentD -->|1. Pull Vetted References| RagFetch[Query Knowledge Base RAG]
    RagFetch -->|2. Jargon Transformation| InlineAnalogy[Substitute terms with inline analogies<br>e.g., compound interest -> snowball effect]
    InlineAnalogy --> ReturnLit[Return Coach Explanation]
    ReturnLit --> EndLit([Done: Answer Returned])

    %% Wallet Flow
    DirectWallet --> FetchDb[Fetch Balance & Transaction Ledger]
    FetchDb --> ReturnWallet[Return Balance & History Details]
    ReturnWallet --> EndWallet([Done: Wallet Info Returned])

    %% Direct Fraud Check
    AgentC_Direct --> RunRisk[Evaluate Composite Risk Score]
    RunRisk --> ReturnRisk[Return Risk Metrics & Decision Plan]
    ReturnRisk --> EndFraud([Done: Fraud Metrics Returned])
```

---

## 🗄️ SQLite Database Schema

The local SQLite sandbox has the following relational schema:

```sql
-- Wallet accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    currency TEXT NOT NULL DEFAULT 'USD',
    balance REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transaction ledger (live ledger)
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    amount REAL NOT NULL,
    merchant TEXT NOT NULL,
    category TEXT NOT NULL,
    location TEXT NOT NULL,
    velocity_mins INTEGER NOT NULL,
    risk_score REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING_HITL', 'APPROVED', 'REJECTED', 'COMPLETED')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES accounts(id)
);

-- Agent memory persistence
CREATE TABLE IF NOT EXISTS agent_memory (
    session_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    memory_key TEXT NOT NULL,
    memory_value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, agent_id, memory_key)
);
```

---

## ⚡ Multi-Agent Execution Path Detailed

### 1. The Expense & Fraud Pipeline (Agent B ➔ Agent C)
* When logging an expense (e.g. *"Spent $5200 on an expensive diamond ring in a Suspicious Location"*), it triggers Agent B.
* Agent B extracts structured details and passes them back to the Orchestrator, which forwards them to Agent C.
* Agent C flags the high amount (+$5000) and suspicious location, yielding an **81% risk score**. Since this exceeds **75%**, it immediately triggers the `PENDING_HITL` state.
* Only after calling the `/transactions/approve` API is the wallet balance updated.

### 2. The Literacy Pipeline (Agent D)
* When asking *"Explain compound interest and liquidity"*, Agent D retrieves definitions from the database knowledge base and processes the text to inject analogies inline, returning the coach response.
