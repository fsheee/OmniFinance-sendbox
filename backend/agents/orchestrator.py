from typing import Dict, Any, Optional
import os
import json
import httpx
from database import db
from agents.expense_tracker import ExpenseTrackerAgent
from agents.fraud_detector import FraudDetectionAgent
from agents.literacy_coach import FinancialLiteracyCoach

class CentralOrchestrator:
    def __init__(self):
        self.expense_tracker = ExpenseTrackerAgent()
        self.fraud_detector = FraudDetectionAgent()
        self.literacy_coach = FinancialLiteracyCoach()
        
    def classify_intent(self, user_prompt: str) -> str:
        """
        Classifies user prompt intent to delegate to specialized sub-agents.
        Returns one of: WALLET, TRANSFER, EXPENSE, FINANCIAL_EDUCATION.
        """
        p_lower = user_prompt.lower()

        # 1. Wallet balance and history query — highest priority
        wallet_words = ["balance", "wallet", "transactions", "ledger", "statement", "history", "how much money"]
        if any(w in p_lower for w in wallet_words):
            self._log_classification(user_prompt, "WALLET", "wallet keyword match")
            return "WALLET"

        # 2. Transfer/send money actions → Fraud Detection Agent
        # Only match explicit transfer language, not general financial terms
        transfer_keywords = [
            "transfer ", " send ", " wire ", "send money", "send $",
            "wire money", "from my account to", "to another account",
            "transferring", "transfered",
        ]
        if any(w in p_lower for w in transfer_keywords):
            self._log_classification(user_prompt, "TRANSFER", "transfer keyword match")
            return "TRANSFER"

        # 3. Try Gemini API for nuanced classification (if key is configured)
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                result = self._classify_with_gemini(user_prompt, api_key)
                if result:
                    self._log_classification(user_prompt, result, "Gemini classification")
                    return result
            except Exception as e:
                print(f"[INTENT] Gemini error: {e}")

        # 4. Rule-based fallback
        return self._classify_rule_based(user_prompt)

    def _log_classification(self, prompt: str, intent: str, source: str) -> None:
        print(f"[INTENT] Input: '{prompt}' -> {intent} ({source})")

    def _classify_with_gemini(self, prompt: str, api_key: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

        system_instruction = (
            "You are a routing classification system. Classify the user's intent into exactly one of:\n"
            "'EXPENSE', 'TRANSFER', 'FINANCIAL_EDUCATION', or 'WALLET'.\n\n"
            "- Choose 'TRANSFER' if the user explicitly wants to send, wire, or move money to another person "
            "or account (e.g., 'transfer $10000 to John', 'send $500 to mom'). "
            "Do NOT choose TRANSFER for general spending, paying bills, or asking how to pay something.\n"
            "- Choose 'EXPENSE' if the user is logging a purchase, buying something, paying for something, "
            "or recording money they spent (e.g., 'spent $45 on lunch', 'bought groceries', 'buy $400 vegetables', "
            "'paid for pizza', 'spent $500 for pay fee').\n"
            "- Choose 'FINANCIAL_EDUCATION' if the user is asking a question, seeking advice, or wants an "
            "explanation about financial concepts, how to pay installments, budgeting, loans, credit, etc. "
            "(e.g., 'what is compound interest', 'how to pay installment monthly', 'explain inflation', "
            "'how does credit work', 'difference between savings and checking').\n"
            "- Choose 'WALLET' if they are asking about their current balance, account statement, "
            "wallet, or transaction history (e.g., 'show my balance', 'wallet').\n\n"
            "IMPORTANT: Questions about how to do something financial (payments, installments, budgeting) "
            "are FINANCIAL_EDUCATION, NOT TRANSFER.\n\n"
            "Respond with ONLY one word: EXPENSE, TRANSFER, FINANCIAL_EDUCATION, or WALLET."
        )
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\nUser prompt: \"{prompt}\""}]}]
        }

        response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
        response.raise_for_status()
        result_json = response.json()
        classification = result_json["candidates"][0]["content"]["parts"][0]["text"].strip().upper()

        if classification in ["EXPENSE", "TRANSFER", "FINANCIAL_EDUCATION", "WALLET"]:
            return classification
        return ""

    def _classify_rule_based(self, prompt: str) -> str:
        p_lower = prompt.lower()

        # Expense tracking
        expense_words = [
            "spent", "bought", "paid", "buy", "purchase", "shopping",
            "grocery", "pizza", "eat", "lunch", "dinner", "food",
            "vegetable", "restaurant", "coffee", "snack", "meal",
            "ordered", "paid for", "spending",
        ]
        if any(w in p_lower for w in expense_words):
            self._log_classification(prompt, "EXPENSE", "expense keyword match")
            return "EXPENSE"

        # Financial education
        literacy_words = [
            "explain", "what is", "how does", "how do", "how to", "how can",
            "define", "what does", "tell me about", "meaning of",
            "what are", "what's ", "difference between", "example of",
            "installment", "monthly payment", "emi", "loan", "credit",
            "interest", "budget", "saving", "investment",
        ]
        if any(w in p_lower for w in literacy_words):
            self._log_classification(prompt, "FINANCIAL_EDUCATION", "education keyword match")
            return "FINANCIAL_EDUCATION"

        # Default fallback to education (safe default: explain financial concepts)
        self._log_classification(prompt, "FINANCIAL_EDUCATION", "default fallback")
        return "FINANCIAL_EDUCATION"

    def route_and_execute(self, user_prompt: str, session_id: str = "sandbox_session") -> Dict[str, Any]:
        """
        The ADK multi-agent routing loop. Resolves dependencies and delegates tasks.
        """
        intent = self.classify_intent(user_prompt)
        
        # Persist orchestrator state to agent memory
        db.save_agent_memory(session_id, "central_orchestrator", "last_intent", intent)
        
        if intent == "EXPENSE":
            # Delegate to Agent B (Expense Tracker)
            tracker_result = self.expense_tracker.execute(user_prompt)
            tool_call = tracker_result["tool_call"]
            payload = tool_call["payload"]
            
            # Sub-agent Routing: Route transaction details through Agent C (Fraud Detector)
            # Before executing the database insertion, compute risk.
            # Location already extracted by expense_tracker. Use it with fallback.
            location = payload.get("location", "Home Location")
            velocity_mins = 1  # Mock short velocity if user submits consecutive logs

            fraud_result = self.fraud_detector.execute({
                "id": payload["id"],
                "amount": payload["amount"],
                "location": location,
                "velocity_mins": velocity_mins
            })
            
            fraud_decision = fraud_result["evaluation"]["decision"]
            risk_score = fraud_result["evaluation"]["risk_score"]
            
            status = "COMPLETED"
            if fraud_decision == "PAUSE_FOR_HITL":
                status = "PENDING_HITL"
                
            # Execute database tool log_transaction
            logged_tx = db.log_transaction(
                tx_id=payload["id"],
                account_id=payload["account_id"],
                amount=payload["amount"],
                merchant=payload["merchant"],
                category=payload["category"],
                location=location,
                velocity_mins=velocity_mins,
                risk_score=risk_score,
                status=status
            )
            
            return {
                "intent": "EXPENSE",
                "agent": "Expense Tracker Agent",
                "status": "PAUSED_WAITING_FOR_HITL" if status == "PENDING_HITL" else "SUCCESS",
                "data": {
                    "transaction": logged_tx,
                    "fraud_evaluation": fraud_result["evaluation"]
                },
                "message": (
                    f"Transaction of ${payload['amount']} at {payload['merchant']} is PAUSED for human approval due to "
                    f"high fraud risk ({risk_score}%)." if status == "PENDING_HITL" else 
                    f"Successfully logged expense: ${payload['amount']} at {payload['merchant']} (Category: {payload['category']})."
                )
            }
            
        elif intent == "TRANSFER":
            import re
            amounts = re.findall(r"\d+", user_prompt)
            amount = float(amounts[0]) if amounts else 100.0

            location = "Suspicious Location" if "suspicious" in user_prompt.lower() else "Home Location"
            velocity = 1 if "fast" in user_prompt.lower() or "quick" in user_prompt.lower() else 30

            evaluation = self.fraud_detector.evaluate_fraud_risk(amount, location, velocity)
            return {
                "intent": "TRANSFER",
                "agent": "Transfer Router Pipeline",
                "status": "SUCCESS",
                "data": {
                    "evaluation": evaluation,
                    "input_parameters": {
                        "amount": amount,
                        "location": location,
                        "velocity_mins": velocity
                    }
                },
                "message": f"Fraud risk evaluation completed. Risk Score: {evaluation['risk_score']}%. Decision: {evaluation['decision']}."
            }

        elif intent == "FINANCIAL_EDUCATION":
            coach_result = self.literacy_coach.execute(user_prompt)
            return {
                "intent": "FINANCIAL_EDUCATION",
                "agent": "Financial Literacy Coach",
                "status": "SUCCESS",
                "data": {
                    "response": coach_result["response"],
                    "references": coach_result["knowledge_base_references"
                    ]
                },
                "message": coach_result["response"]
            }
            
        elif intent == "WALLET":
            # Process directly via wallet tools
            account = db.get_account("account_123")
            txs = db.get_transactions("account_123", limit=5)
            
            balance_str = f"${account['balance']:.2f} {account['currency']}" if account else "$0.00 USD"
            tx_lines = []
            for tx in txs:
                tx_lines.append(f"- [{tx['timestamp']}] {tx['merchant']}: -${tx['amount']} ({tx['status']})")
                
            history_str = "\n".join(tx_lines) if tx_lines else "No transaction history found."
            
            return {
                "intent": "WALLET",
                "agent": "Central Orchestrator",
                "status": "SUCCESS",
                "data": {
                    "account": account,
                    "recent_transactions": txs
                },
                "message": f"Your current balance is {balance_str}.\n\nRecent Transactions:\n{history_str}"
            }
            
        return {
            "intent": "UNKNOWN",
            "agent": "Central Orchestrator",
            "status": "ERROR",
            "message": "Sorry, I could not classify your query. Please ask me about balance, expenses, or financial literacy."
        }
