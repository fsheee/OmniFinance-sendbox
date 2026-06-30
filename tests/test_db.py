import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from database import db
from database.db import DB_FILE


@pytest.fixture(autouse=True)
def clean_db():
    db.reset_db()
    yield


def test_init_db_creates_account():
    account = db.get_account("account_123")
    assert account is not None
    assert account["balance"] == 5000.0
    assert account["currency"] == "USD"


def test_get_account_nonexistent():
    assert db.get_account("nonexistent") is None


def test_log_completed_transaction_deducts_balance():
    db.log_transaction("tx1", "account_123", 100, "Test", "General", "NYC", 0, 10.0, "COMPLETED")
    account = db.get_account("account_123")
    assert account["balance"] == 4900.0


def test_log_pending_hitl_does_not_deduct():
    db.log_transaction("tx2", "account_123", 5000, "Ring", "Shopping", "Remote", 0, 90.0, "PENDING_HITL")
    account = db.get_account("account_123")
    assert account["balance"] == 5000.0


def test_handle_hitl_approval_deducts():
    db.log_transaction("tx3", "account_123", 200, "Item", "Shopping", "NYC", 0, 80.0, "PENDING_HITL")
    db.handle_hitl_approval("tx3", approve=True)
    account = db.get_account("account_123")
    assert account["balance"] == 4800.0
    tx = db.get_transaction("tx3")
    assert tx["status"] == "APPROVED"


def test_handle_hitl_reject_does_not_deduct():
    db.log_transaction("tx4", "account_123", 300, "Item", "Shopping", "NYC", 0, 80.0, "PENDING_HITL")
    db.handle_hitl_approval("tx4", approve=False)
    account = db.get_account("account_123")
    assert account["balance"] == 5000.0
    tx = db.get_transaction("tx4")
    assert tx["status"] == "REJECTED"


def test_handle_hitl_already_resolved_raises():
    db.log_transaction("tx5", "account_123", 100, "Item", "Shopping", "NYC", 0, 80.0, "COMPLETED")
    with pytest.raises(ValueError, match="not in PENDING_HITL"):
        db.handle_hitl_approval("tx5", approve=True)


def test_get_transactions_returns_ordered():
    db.log_transaction("tx_a", "account_123", 10, "A", "Food", "NYC", 0, 0, "COMPLETED")
    db.log_transaction("tx_b", "account_123", 20, "B", "Food", "NYC", 0, 0, "COMPLETED")
    txs = db.get_transactions("account_123", limit=10)
    assert len(txs) == 2


def test_agent_memory():
    db.save_agent_memory("sess1", "agent1", "key1", "value1")
    assert db.get_agent_memory("sess1", "agent1", "key1") == "value1"
    assert db.get_agent_memory("sess1", "agent1", "nonexistent") is None


def test_save_agent_memory_overwrites():
    db.save_agent_memory("sess1", "agent1", "key1", "old")
    db.save_agent_memory("sess1", "agent1", "key1", "new")
    assert db.get_agent_memory("sess1", "agent1", "key1") == "new"


def test_reset_db():
    db.log_transaction("tx1", "account_123", 100, "Test", "General", "NYC", 0, 10.0, "COMPLETED")
    db.reset_db()
    assert len(db.get_transactions("account_123")) == 0
    account = db.get_account("account_123")
    assert account["balance"] == 5000.0
