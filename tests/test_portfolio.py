"""Tests for portfolio database operations."""

import os
import tempfile
import pytest

from halal_invest.db import database as db_module
from halal_invest.db.portfolio import (
    add_transaction,
    get_holdings,
    get_transactions,
    get_portfolio_summary,
    log_purification,
    get_purification_log,
)


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    """Use a temporary database for each test."""
    test_db = tmp_path / "test_portfolio.db"
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    monkeypatch.setattr(db_module, "DB_DIR", tmp_path)
    yield test_db


class TestAddTransaction:
    def test_buy_transaction(self):
        add_transaction("AAPL", "buy", 10, 150.0, "2025-01-15")
        txns = get_transactions()
        assert len(txns) == 1
        assert txns[0]["ticker"] == "AAPL"
        assert txns[0]["action"] == "buy"
        assert txns[0]["shares"] == 10.0
        assert txns[0]["price"] == 150.0

    def test_sell_transaction(self):
        add_transaction("AAPL", "buy", 10, 150.0, "2025-01-15")
        add_transaction("AAPL", "sell", 5, 200.0, "2025-02-15")
        txns = get_transactions()
        assert len(txns) == 2

    def test_sell_more_than_holdings_raises(self):
        add_transaction("AAPL", "buy", 10, 150.0, "2025-01-15")
        with pytest.raises(ValueError, match="Cannot sell"):
            add_transaction("AAPL", "sell", 20, 200.0, "2025-02-15")

    def test_sell_without_holdings_raises(self):
        with pytest.raises(ValueError, match="Cannot sell"):
            add_transaction("MSFT", "sell", 5, 200.0, "2025-02-15")


class TestGetHoldings:
    def test_single_buy(self):
        add_transaction("AAPL", "buy", 10, 150.0, "2025-01-15")
        holdings = get_holdings()
        assert len(holdings) == 1
        assert holdings[0]["ticker"] == "AAPL"
        assert holdings[0]["shares"] == 10.0
        assert holdings[0]["avg_cost"] == 150.0

    def test_multiple_buys_avg_cost(self):
        add_transaction("AAPL", "buy", 10, 100.0, "2025-01-15")
        add_transaction("AAPL", "buy", 10, 200.0, "2025-02-15")
        holdings = get_holdings()
        assert len(holdings) == 1
        assert holdings[0]["shares"] == 20.0
        assert holdings[0]["avg_cost"] == 150.0  # (1000 + 2000) / 20

    def test_buy_and_sell(self):
        add_transaction("AAPL", "buy", 10, 150.0, "2025-01-15")
        add_transaction("AAPL", "sell", 5, 200.0, "2025-02-15")
        holdings = get_holdings()
        assert len(holdings) == 1
        assert holdings[0]["shares"] == 5.0

    def test_sell_all_removes_from_holdings(self):
        add_transaction("AAPL", "buy", 10, 150.0, "2025-01-15")
        add_transaction("AAPL", "sell", 10, 200.0, "2025-02-15")
        holdings = get_holdings()
        assert len(holdings) == 0

    def test_multiple_tickers(self):
        add_transaction("AAPL", "buy", 10, 150.0, "2025-01-15")
        add_transaction("MSFT", "buy", 5, 300.0, "2025-01-15")
        holdings = get_holdings()
        assert len(holdings) == 2


class TestPortfolioSummary:
    def test_summary(self):
        add_transaction("AAPL", "buy", 10, 150.0, "2025-01-15")
        add_transaction("MSFT", "buy", 5, 300.0, "2025-01-15")
        summary = get_portfolio_summary()
        assert summary["total_holdings"] == 2
        assert summary["total_invested"] == 10 * 150.0 + 5 * 300.0


class TestPurification:
    def test_log_purification(self):
        amount = log_purification("AAPL", 2.5, 100.0)
        assert amount == 2.5  # 100 * (2.5 / 100)

    def test_purification_log(self):
        log_purification("AAPL", 2.5, 100.0)
        log_purification("MSFT", 1.0, 200.0)
        logs = get_purification_log()
        assert len(logs) == 2
