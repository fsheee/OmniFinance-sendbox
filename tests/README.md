# Unit Tests

## Run

```bash
pytest tests/ -v                          # all tests
pytest tests/ -v --ignore=tests/test_vector_store.py --ignore=tests/test_knowledge_search.py  # fast tests only (~4s)
pytest tests/test_db.py -v                # database only
pytest tests/test_orchestrator.py -v      # orchestrator only
```

## Summary (49 fast + 12 slow = 60 total)

| File | Tests | What it covers |
|------|-------|----------------|
| `test_db.py` | 11 | CRUD, balance deductions, HITL approval/reject, agent memory, reset |
| `test_expense_tracker.py` | 13 | Amount/merchant/category parsing, location extraction, timestamps |
| `test_fraud_detector.py` | 10 | Risk scoring thresholds, HITL trigger, location/velocity/amount risk |
| `test_orchestrator.py` | 15 | Intent classification (all 4 types), full routing flows, HITL trigger |
| `test_vector_store.py` | 6 | ChromaDB seeding, search, idempotency, score ordering |
| `test_knowledge_search.py` | 5 | API endpoint validation (422, results, fields, ordering) |
