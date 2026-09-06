"""Test suite for the VOLTEX backend.

Run with pytest (needs a PostgreSQL test database):
    pytest -m unit          # pure logic, no DB
    pytest -m integration   # requires DATABASE_URL for a scratch DB
"""

# Tests are grouped by concern: auth, rbac, business rules, transactions.