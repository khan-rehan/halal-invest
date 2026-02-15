"""Tests for display formatting functions."""

from halal_invest.display.tables import (
    format_halal_status,
    format_pass_fail,
    format_percentage,
    format_currency,
    format_ratio,
)


class TestFormatHalalStatus:
    def test_pass(self):
        assert "HALAL" in format_halal_status("PASS")
        assert "green" in format_halal_status("PASS")

    def test_fail(self):
        assert "NOT HALAL" in format_halal_status("FAIL")
        assert "red" in format_halal_status("FAIL")

    def test_doubtful(self):
        assert "DOUBTFUL" in format_halal_status("DOUBTFUL")
        assert "yellow" in format_halal_status("DOUBTFUL")

    def test_error(self):
        assert "ERROR" in format_halal_status("ERROR")


class TestFormatPassFail:
    def test_pass(self):
        assert "PASS" in format_pass_fail(True)
        assert "green" in format_pass_fail(True)

    def test_fail(self):
        assert "FAIL" in format_pass_fail(False)
        assert "red" in format_pass_fail(False)


class TestFormatPercentage:
    def test_positive(self):
        assert format_percentage(0.1234) == "12.34%"

    def test_negative(self):
        assert format_percentage(-0.05) == "-5.00%"

    def test_none(self):
        assert format_percentage(None) == "N/A"

    def test_zero(self):
        assert format_percentage(0.0) == "0.00%"


class TestFormatCurrency:
    def test_billions(self):
        assert format_currency(1_500_000_000) == "$1.50B"

    def test_millions(self):
        assert format_currency(250_000_000) == "$250.00M"

    def test_thousands(self):
        assert format_currency(45_000) == "$45.00K"

    def test_small(self):
        assert format_currency(99.50) == "$99.50"

    def test_negative(self):
        assert format_currency(-1_000_000) == "-$1.00M"

    def test_none(self):
        assert format_currency(None) == "N/A"


class TestFormatRatio:
    def test_normal(self):
        assert format_ratio(1.5) == "1.50"

    def test_zero(self):
        assert format_ratio(0.0) == "0.00"

    def test_none(self):
        assert format_ratio(None) == "N/A"
