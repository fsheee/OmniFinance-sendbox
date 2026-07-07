import pytest
from agents.fraud_detector import FraudDetectionAgent


@pytest.fixture
def fraud_agent():
    return FraudDetectionAgent()


class TestFraudDetectionAgent:
    """Tests for FraudDetectionAgent.evaluate_fraud_risk() and HITL routing."""

    def test_low_risk_transaction(self, fraud_agent):
        """Low-risk: small amount, home location, slow velocity."""
        result = fraud_agent.evaluate_fraud_risk(
            amount=20.0,
            location="Home Location",
            velocity_mins=60
        )
        assert result["risk_score"] < 30.0
        assert result["is_high_risk"] is False
        assert result["decision"] == "ALLOW"
        assert result["metrics"]["amount_risk"] == 0.05
        assert result["metrics"]["velocity_risk"] == 0.0
        assert result["metrics"]["location_risk"] == 0.0

    def test_medium_risk_transaction(self, fraud_agent):
        """Medium-risk: moderate amount, unverified location, moderate velocity."""
        result = fraud_agent.evaluate_fraud_risk(
            amount=800.0,
            location="unverified",
            velocity_mins=5
        )
        assert 30.0 <= result["risk_score"] <= 75.0
        assert result["is_high_risk"] is False
        assert result["decision"] == "ALLOW"
        assert result["metrics"]["amount_risk"] == 0.3
        assert result["metrics"]["location_risk"] == 0.5

    def test_high_risk_transaction(self, fraud_agent):
        """High-risk: large amount, unknown location, fast velocity."""
        result = fraud_agent.evaluate_fraud_risk(
            amount=6000.0,
            location="unknown",
            velocity_mins=1
        )
        assert result["risk_score"] > 75.0
        assert result["is_high_risk"] is True
        assert result["decision"] == "PAUSE_FOR_HITL"
        assert result["metrics"]["amount_risk"] == 0.9
        assert result["metrics"]["location_risk"] == 0.9
        assert result["metrics"]["velocity_risk"] == 0.8

    def test_high_risk_foreign_location(self, fraud_agent):
        """High-risk: foreign location triggers location_risk=0.9."""
        result = fraud_agent.evaluate_fraud_risk(
            amount=100.0,
            location="foreign",
            velocity_mins=60
        )
        assert result["risk_score"] > 30.0
        assert result["metrics"]["location_risk"] == 0.9

    def test_high_risk_north_korea_location(self, fraud_agent):
        """High-risk: sanctioned country triggers location_risk=0.9, combined with high velocity exceeds threshold."""
        result = fraud_agent.evaluate_fraud_risk(
            amount=1000.0,
            location="North Korea",
            velocity_mins=1
        )
        assert result["risk_score"] > 75.0
        assert result["is_high_risk"] is True
        assert result["decision"] == "PAUSE_FOR_HITL"
        assert result["metrics"]["location_risk"] == 0.9

    def test_hitl_routing_low_risk(self, fraud_agent):
        """HITL routing: low risk should NOT trigger PAUSE_FOR_HITL."""
        result = fraud_agent.evaluate_fraud_risk(
            amount=10.0,
            location="Home Location",
            velocity_mins=120
        )
        assert result["decision"] == "ALLOW"
        assert result["is_high_risk"] is False

    def test_hitl_routing_high_risk(self, fraud_agent):
        """HITL routing: high risk should trigger PAUSE_FOR_HITL."""
        result = fraud_agent.evaluate_fraud_risk(
            amount=10000.0,
            location="unknown",
            velocity_mins=1
        )
        assert result["decision"] == "PAUSE_FOR_HITL"
        assert result["is_high_risk"] is True

    def test_boundary_risk_just_below_threshold(self, fraud_agent):
        """Boundary: risk just below HITL threshold (75%)."""
        result = fraud_agent.evaluate_fraud_risk(
            amount=1800.0,
            location="unverified",
            velocity_mins=15
        )
        assert result["risk_score"] <= 75.0
        assert result["is_high_risk"] is False
        assert result["decision"] == "ALLOW"

    def test_suspicious_location_scoring(self, fraud_agent):
        """Location: 'suspicious' keyword should set location_risk=0.7."""
        result = fraud_agent.evaluate_fraud_risk(
            amount=100.0,
            location="Suspicious Location",
            velocity_mins=60
        )
        assert result["metrics"]["location_risk"] == 0.7

    def test_international_location_scoring(self, fraud_agent):
        """Location: 'international' keyword should set location_risk=0.5."""
        result = fraud_agent.evaluate_fraud_risk(
            amount=100.0,
            location="International Transfer",
            velocity_mins=60
        )
        assert result["metrics"]["location_risk"] == 0.5
