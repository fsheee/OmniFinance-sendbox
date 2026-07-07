import uuid
import logging
from typing import Dict, Any, Optional
import os
import json
import httpx
from database import db
from agents.expense_tracker import ExpenseTrackerAgent
from agents.fraud_detector import FraudDetectionAgent
from agents.literacy_coach import FinancialLiteracyCoach

logger = logging.getLogger("omnifinance.orchestrator")

class CentralOrchestrator:
    def __init__(self):
        self.expense_tracker = ExpenseTrackerAgent()
        self.fraud_detector = FraudDetectionAgent()
        self.literacy_coach = FinancialLiteracyCoach()
        
    def classify_intent(self, user_prompt: str) -> str:
        """
        Classifies user prompt intent to delegate to specialized sub-agents.
        Uses Gemini if key exists, otherwise falls back to keyword matching.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                return self._classify_with_gemini(user_prompt, api_key)
            except Exception:
                pass
        return self._classify_rule_based(user_prompt)

    def _classify_with_gemini(self, prompt: str, api_key: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        system_instruction = (
            "You are a routing classification system. Your job is to classify the user's intent "
            "into one of the following exact strings: 'EXPENSE', 'TRANSFER', 'FRAUD', 'LITERACY', or 'WALLET'.\n\n"
            "- Choose 'TRANSFER' if the user wants to transfer or send money to someone "
            "(e.g., 'transfer $100 to John', 'send money to Mom').\n"
            "- Choose 'EXPENSE' if the user is logging a purchase, expense, or telling you they spent money "
            "(e.g., 'spent $45 on lunch', 'log $20 Starbucks').\n"
            "- Choose 'FRAUD' if they are asking about fraud evaluation, suspicious charges, or risk scoring.\n"
            "- Choose 'LITERACY' if they are asking about financial coaching, definitions (liquidity, compound interest), "
            "wealth building, budgeting guides, etc.\n"
            "- Choose 'WALLET' if they are asking about their wallet, balance, or list of past transactions.\n\n"
            "Respond with ONLY one word: EXPENSE, TRANSFER, FRAUD, LITERACY, or WALLET."
        )
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\nUser prompt: \"{prompt}\""}]}]
        }
        
        response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
        response.raise_for_status()
        result_json = response.json()
        classification = result_json["candidates"][0]["content"]["parts"][0]["text"].strip().upper()
        
        if classification in ["EXPENSE", "TRANSFER", "FRAUD", "LITERACY", "WALLET"]:
            return classification
        return self._classify_rule_based(prompt)

    def _classify_rule_based(self, prompt: str) -> str:
        p_lower = prompt.lower()
        
        # 1. Wallet balance and history query detection
        wallet_words = ["balance", "wallet", "transactions", "ledger", "statement", "history", "how much money"]
        if any(w in p_lower for w in wallet_words):
            return "WALLET"
            
        # 2. Transfer detection (check before expense to route correctly)
        transfer_words = ["transfer", "send money", "send ", "wire", "zelle", "venmo"]
        if any(w in p_lower for w in transfer_words):
            return "TRANSFER"

        # 3. Expense tracking detection
        expense_words = ["spent", "spent$", "buy", "bought", "purchase", "log transaction", "pay", "paid", "$", "cost"]
        if any(w in p_lower for w in expense_words) or any(char == '$' for char in p_lower):
            return "EXPENSE"
            
        # 4. Financial coaching & education detection
        literacy_words = [
            "compound interest", "liquidity", "diversification", "inflation", 
            "budget", "yield", "allocation", "explain", "coach", "interest", "wealth",
            "emergency fund", "passive income", "risk tolerance", "asset allocation",
            "debt", "compound growth", "financial", "invest", "saving", "portfolio",
            "dividend", "bond", "stock", "retire"
        ]
        if any(w in p_lower for w in literacy_words):
            return "LITERACY"
            
        # 5. Fraud analysis detection
        fraud_words = ["fraud", "suspicious", "risk", "anomaly", "check transaction", "flagged"]
        if any(w in p_lower for w in fraud_words):
            return "FRAUD"
            
        # Default fallback
        return "LITERACY"

    def route_and_execute(self, user_prompt: str, session_id: str = "sandbox_session") -> Dict[str, Any]:
        """
        The ADK multi-agent routing loop. Resolves dependencies and delegates tasks.
        """
        intent = self.classify_intent(user_prompt)
        
        # Persist orchestrator state to agent memory
        db.save_agent_memory(session_id, "central_orchestrator", "last_intent", intent)
        
        if intent == "EXPENSE":
            # Delegate to Agent B (Expense Tracker)
            logger.info(f"Request received: intent=EXPENSE, prompt='{user_prompt[:80]}'")
            tracker_result = self.expense_tracker.execute(user_prompt)
            tool_call = tracker_result["tool_call"]
            payload = tool_call["payload"]
            amount = payload["amount"]
            merchant = payload["merchant"]
            category = payload["category"]
            account_id = payload["account_id"]
            velocity_mins = 1

            # Location detection from user prompt
            p_lower = user_prompt.lower()
            suspicious_loc = ["unknown", "foreign", "overseas", "abroad", "international", "suspicious", "vpn"]
            safe_loc = ["home", "local", "nearby", "karachi", "lahore", "islamabad", "pakistan"]
            if any(kw in p_lower for kw in suspicious_loc):
                location = "unknown"
            elif any(kw in p_lower for kw in safe_loc):
                location = "Home Location"
            else:
                location = "unverified"
            tx_id = payload["id"]

            # Step 1 - Run fraud detection first
            logger.info(f"Fraud agent invoked: {self.fraud_detector.name}")
            fraud_eval = self.fraud_detector.evaluate_fraud_risk(amount, location, velocity_mins)
            risk_score = fraud_eval["risk_score"]
            logger.info(f"Risk score calculated: {risk_score}%")

            agent_used = "Expense Tracker Agent"

            # Step 2 - If risk_score > 75, pause for HITL
            if risk_score > 75:
                logger.info(f"Routing decision: PAUSE_FOR_HITL (risk {risk_score} > 75)")
                logger.info("HITL triggered: transaction paused for human approval")
                logged_tx = db.log_transaction(
                    tx_id=tx_id, account_id=account_id, amount=amount,
                    merchant=merchant, category=category, location=location,
                    velocity_mins=velocity_mins, risk_score=risk_score,
                    status="PENDING_HITL"
                )
                return {
                    "intent": "EXPENSE", "agent": "Expense Tracker Agent",
                    "status": "PAUSED_WAITING_FOR_HITL",
                    "agent_used": agent_used,
                    "risk_score": risk_score,
                    "routing_decision": "PAUSE_FOR_HITL",
                    "transaction_status": "PENDING_HITL",
                    "data": {"transaction": logged_tx, "fraud_evaluation": fraud_eval},
                    "message": f"High risk detected! Transaction paused for human approval. Risk: {risk_score}/100"
                }

            logger.info(f"Routing decision: ALLOW (risk {risk_score} <= 75)")

            # Step 3 - Log transaction (db.py handles balance check internally)
            logged_tx = db.log_transaction(
                tx_id=tx_id, account_id=account_id, amount=amount,
                merchant=merchant, category=category, location=location,
                velocity_mins=velocity_mins, risk_score=risk_score,
                status="COMPLETED"
            )

            if logged_tx["status"] == "PENDING_HITL":
                logger.info(f"HITL triggered: insufficient balance (balance={logged_tx['current_balance']}, requested={amount})")
                return {
                    "intent": "EXPENSE", "agent": "Expense Tracker Agent",
                    "status": "PAUSED_WAITING_FOR_HITL",
                    "agent_used": agent_used,
                    "risk_score": risk_score,
                    "routing_decision": "ALLOW",
                    "transaction_status": "PENDING_HITL",
                    "data": {
                        "transaction": logged_tx, "fraud_evaluation": fraud_eval,
                        "reason": "Insufficient balance"
                    },
                    "message": (
                        f"Insufficient balance! Transaction paused for approval. "
                        f"Balance: ${logged_tx['current_balance']}, Requested: ${amount}"
                    )
                }

            logger.info(f"Transaction completed successfully: ${amount} at {merchant}")
            return {
                "intent": "EXPENSE", "agent": "Expense Tracker Agent",
                "status": "SUCCESS",
                "agent_used": agent_used,
                "risk_score": risk_score,
                "routing_decision": "ALLOW",
                "transaction_status": "COMPLETED",
                "data": {"transaction": logged_tx, "fraud_evaluation": fraud_eval},
                "message": "Transaction completed successfully"
            }

        elif intent == "TRANSFER":
            import re
            logger.info(f"Request received: intent=TRANSFER, prompt='{user_prompt[:80]}'")
            amount_match = re.search(r"\$(\d+(?:\.\d{2})?)", user_prompt)
            amount = float(amount_match.group(1)) if amount_match else 0.0

            recipient = "Recipient"
            recipient_match = re.search(
                r"(?:to|for)\s+([A-Za-z0-9\s'&]+?)(?:\s+(?:from|with|in|\$)\b|$)",
                user_prompt, re.IGNORECASE
            )
            if recipient_match:
                recipient = recipient_match.group(1).strip()

            account_id = "account_123"
            merchant = recipient
            category = "Transfer"
            velocity_mins = 1
            tx_id = str(uuid.uuid4())

            # Location detection from user prompt
            p_lower = user_prompt.lower()
            suspicious_loc = ["unknown", "foreign", "overseas", "abroad", "international", "suspicious", "vpn"]
            safe_loc = ["home", "local", "nearby", "karachi", "lahore", "islamabad", "pakistan"]
            if any(kw in p_lower for kw in suspicious_loc):
                location = "unknown"
            elif any(kw in p_lower for kw in safe_loc):
                location = "Home Location"
            else:
                location = "unverified"

            # Step 1 - Run fraud detection first
            logger.info(f"Fraud agent invoked: {self.fraud_detector.name}")
            fraud_eval = self.fraud_detector.evaluate_fraud_risk(amount, location, velocity_mins)
            risk_score = fraud_eval["risk_score"]
            logger.info(f"Risk score calculated: {risk_score}%")

            agent_used = self.fraud_detector.name

            # Step 2 - If risk_score > 75, pause for HITL
            if risk_score > 75:
                logger.info(f"Routing decision: PAUSE_FOR_HITL (risk {risk_score} > 75)")
                logger.info("HITL triggered: transaction paused for human approval")
                logged_tx = db.log_transaction(
                    tx_id=tx_id, account_id=account_id, amount=amount,
                    merchant=merchant, category=category, location=location,
                    velocity_mins=velocity_mins, risk_score=risk_score,
                    status="PENDING_HITL"
                )
                return {
                    "intent": "TRANSFER", "agent": "Fraud Detection Agent",
                    "status": "PAUSED_WAITING_FOR_HITL",
                    "agent_used": agent_used,
                    "risk_score": risk_score,
                    "routing_decision": "PAUSE_FOR_HITL",
                    "transaction_status": "PENDING_HITL",
                    "data": {"transaction": logged_tx, "fraud_evaluation": fraud_eval},
                    "message": f"High risk detected! Transaction paused for human approval. Risk: {risk_score}/100"
                }

            logger.info(f"Routing decision: ALLOW (risk {risk_score} <= 75)")

            # Step 3 - Log transaction (db.py handles balance check internally)
            logged_tx = db.log_transaction(
                tx_id=tx_id, account_id=account_id, amount=amount,
                merchant=merchant, category=category, location=location,
                velocity_mins=velocity_mins, risk_score=risk_score,
                status="COMPLETED"
            )

            if logged_tx["status"] == "PENDING_HITL":
                logger.info(f"HITL triggered: insufficient balance (balance={logged_tx['current_balance']}, requested={amount})")
                return {
                    "intent": "TRANSFER", "agent": "Fraud Detection Agent",
                    "status": "PAUSED_WAITING_FOR_HITL",
                    "agent_used": agent_used,
                    "risk_score": risk_score,
                    "routing_decision": "ALLOW",
                    "transaction_status": "PENDING_HITL",
                    "data": {
                        "transaction": logged_tx, "fraud_evaluation": fraud_eval,
                        "reason": "Insufficient balance"
                    },
                    "message": (
                        f"Insufficient balance! Transaction paused for approval. "
                        f"Balance: ${logged_tx['current_balance']}, Requested: ${amount}"
                    )
                }

            logger.info(f"Transfer completed successfully: ${amount} to {recipient}")
            return {
                "intent": "TRANSFER", "agent": "Fraud Detection Agent",
                "status": "SUCCESS",
                "agent_used": agent_used,
                "risk_score": risk_score,
                "routing_decision": "ALLOW",
                "transaction_status": "COMPLETED",
                "data": {"transaction": logged_tx, "fraud_evaluation": fraud_eval},
                "message": "Transaction completed successfully"
            }

        elif intent == "FRAUD":
            # Extract basic params for verification
            # Mock risk calculation query
            import re
            amounts = re.findall(r"\d+", user_prompt)
            amount = float(amounts[0]) if amounts else 100.0
            
            location = "Suspicious Location" if "suspicious" in user_prompt.lower() else "Home Location"
            velocity = 1 if "fast" in user_prompt.lower() or "quick" in user_prompt.lower() else 30
            
            evaluation = self.fraud_detector.evaluate_fraud_risk(amount, location, velocity)
            return {
                "intent": "FRAUD", "agent": "Fraud Detection Agent",
                "status": "SUCCESS",
                "agent_used": self.fraud_detector.name,
                "risk_score": evaluation["risk_score"],
                "routing_decision": evaluation["decision"],
                "transaction_status": "PENDING_HITL" if evaluation["is_high_risk"] else "ALLOW",
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
            
        elif intent == "LITERACY":
            # Delegate to Agent D (Financial Literacy Coach)
            coach_result = self.literacy_coach.execute(user_prompt)
            return {
                "intent": "LITERACY", "agent": "Financial Literacy Coach",
                "status": "SUCCESS",
                "data": {
                    "response": coach_result["response"],
                    "references": coach_result["knowledge_base_references"]
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
                "intent": "WALLET", "agent": "Central Orchestrator",
                "status": "SUCCESS",
                "data": {
                    "account": account,
                    "recent_transactions": txs
                },
                "message": f"Your current balance is {balance_str}.\n\nRecent Transactions:\n{history_str}"
            }
            
        return {
            "intent": "UNKNOWN", "agent": "Central Orchestrator",
            "status": "ERROR",
            "message": "Sorry, I could not classify your query. Please ask me about balance, expenses, or financial literacy."
        }
