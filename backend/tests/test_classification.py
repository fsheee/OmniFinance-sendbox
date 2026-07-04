import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.orchestrator import CentralOrchestrator


class TestIntentClassification:

    def setup_method(self):
        self.orchestrator = CentralOrchestrator()

    def test_financial_education_compound_interest(self):
        result = self.orchestrator.classify_intent("What is compound interest?")
        assert result == "FINANCIAL_EDUCATION", f"Expected FINANCIAL_EDUCATION, got {result}"

    def test_financial_education_installment(self):
        result = self.orchestrator.classify_intent("How to pay installment monthly?")
        assert result == "FINANCIAL_EDUCATION", f"Expected FINANCIAL_EDUCATION, got {result}"

    def test_expense_spent_on_groceries(self):
        result = self.orchestrator.classify_intent("spent $50 on groceries")
        assert result == "EXPENSE", f"Expected EXPENSE, got {result}"

    def test_expense_buy_vegetables(self):
        result = self.orchestrator.classify_intent("buy $400 vegetables")
        assert result == "EXPENSE", f"Expected EXPENSE, got {result}"

    def test_transfer_to_john(self):
        result = self.orchestrator.classify_intent("transfer $5000 to John")
        assert result == "TRANSFER", f"Expected TRANSFER, got {result}"

    def test_expense_paid_for_pizza(self):
        result = self.orchestrator.classify_intent("paid $20 for pizza")
        assert result == "EXPENSE", f"Expected EXPENSE, got {result}"

    def test_financial_education_explain_inflation(self):
        result = self.orchestrator.classify_intent("explain inflation")
        assert result == "FINANCIAL_EDUCATION", f"Expected FINANCIAL_EDUCATION, got {result}"

    def test_wallet_balance(self):
        result = self.orchestrator.classify_intent("show my balance")
        assert result == "WALLET", f"Expected WALLET, got {result}"

    def test_expense_bought_lunch(self):
        result = self.orchestrator.classify_intent("bought lunch at subway")
        assert result == "EXPENSE", f"Expected EXPENSE, got {result}"

    def test_transfer_send_money(self):
        result = self.orchestrator.classify_intent("send $500 to mom")
        assert result == "TRANSFER", f"Expected TRANSFER, got {result}"

    def test_expense_spent_fee(self):
        result = self.orchestrator.classify_intent("spent $500 for pay fee")
        assert result == "EXPENSE", f"Expected EXPENSE, got {result}"
