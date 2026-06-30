import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.orchestrator import CentralOrchestrator

orchestrator = CentralOrchestrator()


def test_classify_expense():
    intent = orchestrator.classify_intent("Spent $45 on pizza")
    assert intent == "EXPENSE"


def test_classify_expense_with_dollar():
    intent = orchestrator.classify_intent("I paid $20 for lunch today")
    assert intent == "EXPENSE"


def test_classify_wallet():
    intent = orchestrator.classify_intent("What is my balance?")
    assert intent == "WALLET"


def test_classify_wallet_history():
    intent = orchestrator.classify_intent("Show me my transaction history")
    assert intent == "WALLET"


def test_classify_literacy():
    intent = orchestrator.classify_intent("Explain compound interest")
    assert intent == "LITERACY"


def test_classify_literacy_coach():
    intent = orchestrator.classify_intent("What is liquidity and diversification?")
    assert intent == "LITERACY"


def test_classify_literacy_budget():
    intent = orchestrator.classify_intent("How do I make a budget?")
    assert intent == "LITERACY"


def test_classify_literacy_invest():
    intent = orchestrator.classify_intent("How do I start investing?")
    assert intent == "LITERACY"


def test_classify_fraud():
    intent = orchestrator.classify_intent("Check this transaction for fraud")
    assert intent == "FRAUD"


def test_classify_fraud_suspicious():
    intent = orchestrator.classify_intent("Is this suspicious transaction risky?")
    assert intent == "FRAUD"


def test_classify_default_fallback():
    intent = orchestrator.classify_intent("Hello, how are you?")
    assert intent == "LITERACY"


def test_route_expense_full_flow():
    result = orchestrator.route_and_execute("Spent $45 on pizza with friends")
    assert result["intent"] == "EXPENSE"
    assert result["status"] == "SUCCESS"
    assert "transaction" in result["data"]
    assert "fraud_evaluation" in result["data"]
    assert result["data"]["transaction"]["amount"] == 45.0


def test_route_literacy_full_flow():
    result = orchestrator.route_and_execute("Explain compound interest")
    assert result["intent"] == "LITERACY"
    assert result["status"] == "SUCCESS"
    assert "references" in result["data"]
    assert len(result["data"]["references"]) > 0


def test_route_wallet_full_flow():
    result = orchestrator.route_and_execute("What is my balance?")
    assert result["intent"] == "WALLET"
    assert result["status"] == "SUCCESS"
    assert "account" in result["data"]
    assert result["data"]["account"]["balance"] > 0


def test_route_fraud_full_flow():
    result = orchestrator.route_and_execute("Check suspicious transaction for fraud")
    assert result["intent"] == "FRAUD"
    assert result["status"] == "SUCCESS"
    assert "evaluation" in result["data"]


def test_route_high_risk_triggers_hitl():
    result = orchestrator.route_and_execute("Spent $5200 on a diamond ring in Suspicious Location")
    assert result["intent"] == "EXPENSE"
    assert result["status"] == "PAUSED_WAITING_FOR_HITL"
    assert result["data"]["fraud_evaluation"]["risk_score"] > 75
