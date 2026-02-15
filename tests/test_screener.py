"""Tests for the halal screening logic."""

from halal_invest.core.screener import (
    screen_business_activity,
    screen_debt_ratio,
    screen_liquid_assets_ratio,
    screen_impure_income,
    screen_receivables_ratio,
    HARAM_SECTORS,
    HARAM_INDUSTRIES,
    HARAM_TICKERS,
)


class TestBusinessActivity:
    def test_technology_passes(self):
        info = {"sector": "Technology", "industry": "Consumer Electronics"}
        result = screen_business_activity(info)
        assert result["pass"] is True

    def test_financial_services_fails(self):
        info = {"sector": "Financial Services", "industry": "Banks - Diversified"}
        result = screen_business_activity(info)
        assert result["pass"] is False

    def test_alcohol_industry_fails(self):
        info = {"sector": "Consumer Staples", "industry": "Alcoholic Beverages"}
        result = screen_business_activity(info)
        assert result["pass"] is False

    def test_tobacco_industry_fails(self):
        info = {"sector": "Consumer Staples", "industry": "Tobacco"}
        result = screen_business_activity(info)
        assert result["pass"] is False

    def test_gambling_industry_fails(self):
        info = {"sector": "Consumer Discretionary", "industry": "Casinos & Gaming"}
        result = screen_business_activity(info)
        assert result["pass"] is False

    def test_defense_industry_fails(self):
        info = {"sector": "Industrials", "industry": "Aerospace & Defense"}
        result = screen_business_activity(info)
        assert result["pass"] is False

    def test_brewers_industry_fails(self):
        info = {"sector": "Consumer Defensive", "industry": "Beverages - Brewers"}
        result = screen_business_activity(info)
        assert result["pass"] is False

    def test_wineries_distilleries_fails(self):
        info = {"sector": "Consumer Defensive", "industry": "Beverages - Wineries & Distilleries"}
        result = screen_business_activity(info)
        assert result["pass"] is False

    def test_resorts_casinos_fails(self):
        info = {"sector": "Consumer Cyclical", "industry": "Resorts & Casinos"}
        result = screen_business_activity(info)
        assert result["pass"] is False

    def test_curated_ticker_nflx_fails(self):
        info = {"sector": "Communication Services", "industry": "Entertainment"}
        result = screen_business_activity(info, ticker="NFLX")
        assert result["pass"] is False
        assert "explicit" in result["reason"].lower() or "content" in result["reason"].lower()

    def test_curated_ticker_hon_fails(self):
        info = {"sector": "Industrials", "industry": "Conglomerates"}
        result = screen_business_activity(info, ticker="HON")
        assert result["pass"] is False
        assert "defense" in result["reason"].lower()

    def test_curated_ticker_case_insensitive(self):
        info = {"sector": "Communication Services", "industry": "Entertainment"}
        result = screen_business_activity(info, ticker="nflx")
        assert result["pass"] is False

    def test_non_curated_ticker_passes(self):
        info = {"sector": "Technology", "industry": "Consumer Electronics"}
        result = screen_business_activity(info, ticker="AAPL")
        assert result["pass"] is True

    def test_missing_sector_passes(self):
        info = {}
        result = screen_business_activity(info)
        assert result["pass"] is True


class TestDebtRatio:
    def test_low_debt_passes(self):
        info = {"totalDebt": 100_000, "marketCap": 1_000_000}
        result = screen_debt_ratio(info)
        assert result["pass"] is True
        assert result["value"] < 0.33

    def test_high_debt_fails(self):
        info = {"totalDebt": 500_000, "marketCap": 1_000_000}
        result = screen_debt_ratio(info)
        assert result["pass"] is False
        assert result["value"] >= 0.33

    def test_exact_threshold_fails(self):
        info = {"totalDebt": 330_000, "marketCap": 1_000_000}
        result = screen_debt_ratio(info)
        assert result["pass"] is False

    def test_missing_data_assumed_compliant(self):
        info = {}
        result = screen_debt_ratio(info)
        assert result["pass"] is True
        assert result["value"] is None

    def test_zero_market_cap_assumed_compliant(self):
        info = {"totalDebt": 100_000, "marketCap": 0}
        result = screen_debt_ratio(info)
        assert result["pass"] is True


class TestLiquidAssetsRatio:
    def test_low_liquid_assets_passes(self):
        info = {"totalCash": 100_000, "shortTermInvestments": 50_000, "marketCap": 1_000_000}
        result = screen_liquid_assets_ratio(info)
        assert result["pass"] is True

    def test_high_liquid_assets_fails(self):
        info = {"totalCash": 300_000, "shortTermInvestments": 100_000, "marketCap": 1_000_000}
        result = screen_liquid_assets_ratio(info)
        assert result["pass"] is False

    def test_missing_data_passes(self):
        info = {}
        result = screen_liquid_assets_ratio(info)
        assert result["pass"] is True


class TestImpureIncome:
    def test_no_interest_income_passes(self):
        info = {"interestExpense": 0, "totalRevenue": 1_000_000}
        result = screen_impure_income(info)
        assert result["pass"] is True

    def test_high_interest_fails(self):
        info = {"interestExpense": -100_000, "totalRevenue": 1_000_000}
        result = screen_impure_income(info)
        assert result["pass"] is False

    def test_low_interest_passes(self):
        info = {"interestExpense": -10_000, "totalRevenue": 1_000_000}
        result = screen_impure_income(info)
        assert result["pass"] is True

    def test_interest_income_used_when_higher(self):
        # interestIncome is higher than interestExpense, should use it
        info = {"interestExpense": -10_000, "interestIncome": 80_000, "totalRevenue": 1_000_000}
        result = screen_impure_income(info)
        assert result["pass"] is False
        assert result["value"] == 80_000 / 1_000_000

    def test_missing_revenue_assumed_compliant(self):
        info = {}
        result = screen_impure_income(info)
        assert result["pass"] is True


class TestReceivablesRatio:
    def test_low_receivables_passes(self):
        info = {"netReceivables": 100_000, "marketCap": 1_000_000}
        result = screen_receivables_ratio(info)
        assert result["pass"] is True
        assert result["value"] < 0.33

    def test_high_receivables_fails(self):
        info = {"netReceivables": 400_000, "marketCap": 1_000_000}
        result = screen_receivables_ratio(info)
        assert result["pass"] is False
        assert result["value"] >= 0.33

    def test_missing_data_marked_doubtful(self):
        info = {}
        result = screen_receivables_ratio(info)
        assert result["pass"] is True
        assert result["value"] is None

    def test_zero_market_cap(self):
        info = {"netReceivables": 100_000, "marketCap": 0}
        result = screen_receivables_ratio(info)
        assert result["pass"] is True
        assert result["value"] is None
