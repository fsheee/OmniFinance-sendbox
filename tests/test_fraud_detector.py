import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.fraud_detector import FraudDetectionAgent

agent = FraudDetectionAgent()


def test_low_risk_small_amount_home():
    result = agent.evaluate_fraud_risk(amount=45.0, location="Home Location", velocity_mins=60)
    assert result["risk_score"] < 20
    assert result["decision"] == "ALLOW"
    assert result["is_high_risk"] is False


def test_high_risk_large_amount():
    result = agent.evaluate_fraud_risk(amount=5000.0, location="Home Location", velocity_mins=60)
    assert result["risk_score"] > 20
    assert result["metrics"]["amount_risk"] == 0.9


def test_high_risk_suspicious_location():
    result = agent.evaluate_fraud_risk(amount=100.0, location="Suspicious Location", velocity_mins=60)
    assert result["metrics"]["location_risk"] == 0.7
    assert result["is_high_risk"] is False


def test_hitl_triggered_above_75():
    result = agent.evaluate_fraud_risk(amount=5000.0, location="Suspicious Location", velocity_mins=1)
    assert result["risk_score"] > 75
    assert result["decision"] == "PAUSE_FOR_HITL"
    assert result["is_high_risk"] is True


def test_high_risk_country():
    result = agent.evaluate_fraud_risk(amount=100.0, location="North Korea", velocity_mins=60)
    assert result["metrics"]["location_risk"] == 0.9
    assert result["is_high_risk"] is False


def test_velocity_risk_immediate():
    result = agent.evaluate_fraud_risk(amount=50.0, location="Home Location", velocity_mins=1)
    assert result["metrics"]["velocity_risk"] == 0.8


def test_velocity_risk_moderate():
    r1 = agent.evaluate_fraud_risk(50.0, "Home", 5)
    assert r1["metrics"]["velocity_risk"] == 0.5
    r2 = agent.evaluate_fraud_risk(50.0, "Home", 15)
    assert r2["metrics"]["velocity_risk"] == 0.2
    r3 = agent.evaluate_fraud_risk(50.0, "Home", 60)
    assert r3["metrics"]["velocity_risk"] == 0.0


def test_amount_risk_thresholds():
    r1 = agent.evaluate_fraud_risk(100.0, "Home", 60)
    assert r1["metrics"]["amount_risk"] == 0.05
    r2 = agent.evaluate_fraud_risk(500.0, "Home", 60)
    assert r2["metrics"]["amount_risk"] == 0.3
    r3 = agent.evaluate_fraud_risk(1000.0, "Home", 60)
    assert r3["metrics"]["amount_risk"] == 0.5
    r4 = agent.evaluate_fraud_risk(5000.0, "Home", 60)
    assert r4["metrics"]["amount_risk"] == 0.9


def test_execute_passes_fields():
    result = agent.execute({"id": "tx-1", "amount": 100.0, "location": "Home", "velocity_mins": 30})
    assert result["transaction_id"] == "tx-1"
    assert "evaluation" in result
    assert result["evaluation"]["risk_score"] > 0
