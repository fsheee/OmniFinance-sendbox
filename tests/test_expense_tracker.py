import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.expense_tracker import ExpenseTrackerAgent

agent = ExpenseTrackerAgent()


def test_parse_simple_expense():
    result = agent.parse_query("Spent $45 on pizza with friends last night")
    assert result["amount"] == 45.0
    assert result["merchant"] == "Domino's"
    assert result["category"] == "Food & Dining"


def test_parse_large_expense():
    result = agent.parse_query("Spent $5200 on an expensive diamond ring in a Suspicious Location")
    assert result["amount"] == 5200.0
    assert result["merchant"] == "Jeweler"
    assert result["location"] == "Suspicious Location"


def test_parse_with_at_merchant():
    result = agent.parse_query("Paid $20 at Starbucks for coffee")
    assert result["amount"] == 20.0
    assert result["merchant"] == "Starbucks"
    assert result["category"] == "Food & Dining"


def test_parse_with_from_merchant():
    result = agent.parse_query("Bought $150 from Amazon")
    assert result["amount"] == 150.0
    assert result["merchant"] == "Amazon"
    assert result["category"] == "Shopping"


def test_parse_yesterday():
    result = agent.parse_query("Spent $30 on lunch yesterday")
    assert result["amount"] == 30.0


def test_parse_location_in():
    result = agent.parse_query("Spent $10 on coffee in New York")
    assert "new york" in result["location"].lower()


def test_parse_no_amount():
    result = agent.parse_query("Bought groceries")
    assert result["amount"] == 0.0


def test_log_transaction_tool_generates_payload():
    result = agent.log_transaction_tool(amount=50.0, merchant="Test", category="General", timestamp="2025-01-01")
    assert result["action"] == "log_transaction"
    assert result["payload"]["amount"] == 50.0
    assert result["payload"]["merchant"] == "Test"
    assert result["payload"]["category"] == "General"
    assert result["payload"]["account_id"] == "account_123"
    assert "id" in result["payload"]


def test_execute_returns_expected_structure():
    result = agent.execute("Spent $75 at Restaurant for dinner")
    assert "agent" in result
    assert "parsed_details" in result
    assert "tool_call" in result
    assert result["tool_call"]["payload"]["amount"] == 75.0


def test_categorize_transportation():
    result = agent.parse_query("Paid $25 for Uber ride")
    assert result["category"] == "Transportation"


def test_categorize_entertainment():
    result = agent.parse_query("Spent $15 on Netflix")
    assert result["category"] == "Entertainment"


def test_categorize_utilities():
    result = agent.parse_query("Paid $100 for electricity bill")
    assert result["category"] == "Utilities"


def test_parse_merchant_fallsback_to_unknown():
    result = agent.parse_query("Paid $100 for something")
    assert result["merchant"] == "Unknown Merchant"
    assert result["amount"] == 100.0
