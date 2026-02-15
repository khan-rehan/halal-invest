"""Generate PDF reports of halal screening results."""

from datetime import datetime
from pathlib import Path
from fpdf import FPDF


class HalalReportPDF(FPDF):
    """Custom PDF document for halal stock screening reports."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.set_font("Helvetica")

    # ------------------------------------------------------------------
    # Header / Footer
    # ------------------------------------------------------------------

    def header(self):
        """Draw page header with report title and date."""
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, "Halal S&P 500 Daily Screener Report", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, datetime.now().strftime("%A, %B %d, %Y"), new_x="LMARGIN", new_y="NEXT", align="C")
        # Separator line
        self.set_draw_color(0, 128, 0)
        self.set_line_width(0.5)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        """Draw page footer with page numbers."""
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", align="C")
        # Reset text color for next page content
        self.set_text_color(0, 0, 0)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def add_summary_section(
        self,
        total_screened: int,
        total_passed: int,
        total_failed: int,
        total_error: int,
        sector_breakdown: dict,
    ):
        """Add the summary section at the top of the report.

        Args:
            total_screened: Total number of stocks screened.
            total_passed: Number that passed (PASS + DOUBTFUL).
            total_failed: Number that failed.
            total_error: Number with errors.
            sector_breakdown: Mapping of sector name to count of passing stocks.
        """
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        self.set_font("Helvetica", "", 10)
        today = datetime.now().strftime("%Y-%m-%d")
        lines = [
            f"Date: {today}",
            f"Total Screened: {total_screened}",
            f"Passed (Halal): {total_passed}",
            f"Failed: {total_failed}",
            f"Errors: {total_error}",
        ]
        for line in lines:
            self.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

        # Sector breakdown table
        if sector_breakdown:
            self.set_font("Helvetica", "B", 10)
            self.cell(0, 6, "Sector Breakdown (Passing Stocks)", new_x="LMARGIN", new_y="NEXT")
            self.ln(2)

            # Table header
            self.set_font("Helvetica", "B", 9)
            self.set_fill_color(0, 128, 0)
            self.set_text_color(255, 255, 255)
            self.cell(80, 6, "Sector", border=1, fill=True)
            self.cell(30, 6, "Count", border=1, align="C", fill=True)
            self.cell(40, 6, "% of Passed", border=1, align="C", fill=True)
            self.ln()
            self.set_text_color(0, 0, 0)

            # Sort sectors by count descending
            sorted_sectors = sorted(sector_breakdown.items(), key=lambda x: x[1], reverse=True)
            self.set_font("Helvetica", "", 9)

            for idx, (sector, count) in enumerate(sorted_sectors):
                pct = (count / total_passed * 100) if total_passed > 0 else 0.0
                if idx % 2 == 0:
                    self.set_fill_color(240, 240, 240)
                else:
                    self.set_fill_color(255, 255, 255)
                self.cell(80, 5, self._sanitize(sector[:40]), border=1, fill=True)
                self.cell(30, 5, str(count), border=1, align="C", fill=True)
                self.cell(40, 5, f"{pct:.1f}%", border=1, align="C", fill=True)
                self.ln()

        self.ln(6)

    # ------------------------------------------------------------------
    # Individual Stock Section
    # ------------------------------------------------------------------

    def add_stock_section(self, stock_data: dict):
        """Add a compact section for a single stock.

        Args:
            stock_data: Dictionary with keys:
                - ticker (str)
                - company (str)
                - sector (str)
                - industry (str)
                - halal_screens (dict): screening results
                - fundamentals (dict): fundamental metrics
                - signals (dict): technical signal results
        """
        ticker = stock_data.get("ticker", "N/A")
        company = stock_data.get("company", "N/A")
        sector = stock_data.get("sector", "N/A")
        industry = stock_data.get("industry", "N/A")
        halal_screens = stock_data.get("halal_screens", {})
        fundamentals = stock_data.get("fundamentals", {})
        signals = stock_data.get("signals", {})

        # Check if we need a new page (leave at least 60mm for a stock block)
        if self.get_y() > 230:
            self.add_page()

        # Separator line
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

        # Stock header
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(0, 80, 0)
        self.cell(0, 6, self._sanitize(f"{ticker} - {company}"), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 4, self._sanitize(f"{sector} | {industry}"), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        # --- Halal Screening ---
        self._section_label("Halal Screening")
        ba = halal_screens.get("business_activity", {})
        dr = halal_screens.get("debt_ratio", {})
        la = halal_screens.get("liquid_assets_ratio", {})
        ii = halal_screens.get("impure_income", {})

        ba_text = "PASS" if ba.get("pass") else "FAIL"
        dr_val = dr.get("value")
        dr_text = f"{dr_val:.1%} (< 33%)" if dr_val is not None else "N/A"
        la_val = la.get("value")
        la_text = f"{la_val:.1%} (< 33%)" if la_val is not None else "N/A"
        ii_val = ii.get("value")
        ii_text = f"{ii_val:.1%} (< 5%)" if ii_val is not None else "N/A"

        self.set_font("Helvetica", "", 8)
        col_w = 47.5
        self._mini_cell("Business Activity", ba_text, col_w)
        self._mini_cell("Debt Ratio", dr_text, col_w)
        self._mini_cell("Liquid Assets", la_text, col_w)
        self._mini_cell("Impure Income", ii_text, col_w)
        self.ln()

        # --- Valuation ---
        self._section_label("Valuation")
        self.set_font("Helvetica", "", 8)
        val_items = [
            ("P/E", self._format_value(fundamentals.get("pe_ratio"), "ratio")),
            ("Fwd P/E", self._format_value(fundamentals.get("forward_pe"), "ratio")),
            ("P/B", self._format_value(fundamentals.get("pb_ratio"), "ratio")),
            ("PEG", self._format_value(fundamentals.get("peg_ratio"), "ratio")),
            ("EV/EBITDA", self._format_value(fundamentals.get("ev_ebitda"), "ratio")),
        ]
        self._inline_metrics(val_items)

        # --- Profitability ---
        self._section_label("Profitability")
        prof_items = [
            ("Gross Margin", self._format_value(fundamentals.get("gross_margin"), "pct")),
            ("Op Margin", self._format_value(fundamentals.get("operating_margin"), "pct")),
            ("Net Margin", self._format_value(fundamentals.get("net_margin"), "pct")),
            ("ROE", self._format_value(fundamentals.get("roe"), "pct")),
            ("ROA", self._format_value(fundamentals.get("roa"), "pct")),
        ]
        self._inline_metrics(prof_items)

        # --- Growth ---
        self._section_label("Growth")
        growth_items = [
            ("Revenue Growth", self._format_value(fundamentals.get("revenue_growth"), "pct")),
            ("Earnings Growth", self._format_value(fundamentals.get("earnings_growth"), "pct")),
        ]
        self._inline_metrics(growth_items)

        # --- Financial Health ---
        self._section_label("Financial Health")
        health_items = [
            ("Debt/Equity", self._format_value(fundamentals.get("debt_to_equity"), "ratio")),
            ("Current Ratio", self._format_value(fundamentals.get("current_ratio"), "ratio")),
            ("Free Cash Flow", self._format_value(fundamentals.get("free_cash_flow"), "currency")),
        ]
        self._inline_metrics(health_items)

        # --- Dividends ---
        self._section_label("Dividends")
        div_items = [
            ("Yield", self._format_value(fundamentals.get("dividend_yield"), "pct")),
            ("Payout Ratio", self._format_value(fundamentals.get("payout_ratio"), "pct")),
        ]
        self._inline_metrics(div_items)

        # --- Technical Signals ---
        self._section_label("Technical Signals")
        rsi_sig = signals.get("rsi", {}).get("signal", "N/A")
        rsi_val = signals.get("rsi", {}).get("value")
        rsi_text = f"{rsi_val} ({rsi_sig})" if rsi_val is not None else rsi_sig

        macd_sig = signals.get("macd", {}).get("signal", "N/A")
        sma_sig = signals.get("sma_crossover", {}).get("signal", "N/A")
        boll_sig = signals.get("bollinger", {}).get("signal", "N/A")
        overall_sig = signals.get("overall", {}).get("signal", "N/A")

        sig_items = [
            ("RSI", rsi_text),
            ("MACD", macd_sig),
            ("SMA Cross", sma_sig),
            ("Bollinger", boll_sig),
            ("Overall", overall_sig),
        ]
        self._inline_metrics(sig_items)
        self.ln(2)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize(text: str) -> str:
        """Replace non-ASCII characters with safe Latin-1 equivalents."""
        replacements = {
            "\u2014": "--",   # em dash
            "\u2013": "-",    # en dash
            "\u2018": "'",    # left single quote
            "\u2019": "'",    # right single quote
            "\u201c": '"',    # left double quote
            "\u201d": '"',    # right double quote
            "\u2026": "...",  # ellipsis
            "\u2022": "*",    # bullet
            "\u00a0": " ",    # non-breaking space
        }
        for char, repl in replacements.items():
            text = text.replace(char, repl)
        # Fallback: replace any remaining non-latin1 chars
        return text.encode("latin-1", errors="replace").decode("latin-1")

    def _section_label(self, text: str):
        """Print a small bold label for a subsection."""
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(80, 80, 80)
        self.cell(0, 4, text, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def _mini_cell(self, label: str, value: str, width: float):
        """Print a label: value pair in a fixed-width cell (no line break)."""
        self.set_font("Helvetica", "B", 8)
        self.cell(20, 4, self._sanitize(f"{label}:"), align="R")
        self.set_font("Helvetica", "", 8)
        self.cell(width - 20, 4, self._sanitize(f" {value}"))

    def _inline_metrics(self, items: list[tuple[str, str]]):
        """Print a list of (label, value) pairs on a single line."""
        self.set_font("Helvetica", "", 8)
        parts = [f"{label}: {value}" for label, value in items]
        line = "   |   ".join(parts)
        self.cell(0, 4, self._sanitize(line), new_x="LMARGIN", new_y="NEXT")

    def _format_value(self, value, fmt: str = "general") -> str:
        """Format a value for display in the report.

        Args:
            value: The raw value to format.
            fmt: One of 'pct', 'currency', 'ratio', or 'general'.

        Returns:
            A human-readable string representation.
        """
        if value is None:
            return "N/A"

        try:
            value = float(value)
        except (TypeError, ValueError):
            return str(value)

        if fmt == "pct":
            # Values from yfinance are typically already decimals (e.g., 0.25 = 25%)
            if abs(value) < 1:
                return f"{value * 100:.1f}%"
            return f"{value:.1f}%"

        if fmt == "currency":
            abs_val = abs(value)
            sign = "-" if value < 0 else ""
            if abs_val >= 1_000_000_000:
                return f"{sign}${abs_val / 1_000_000_000:.1f}B"
            if abs_val >= 1_000_000:
                return f"{sign}${abs_val / 1_000_000:.1f}M"
            if abs_val >= 1_000:
                return f"{sign}${abs_val / 1_000:.1f}K"
            return f"{sign}${abs_val:.0f}"

        if fmt == "ratio":
            return f"{value:.2f}"

        return str(value)


# ----------------------------------------------------------------------
# Main report generation function
# ----------------------------------------------------------------------


def generate_report(
    screening_results: list[dict],
    output_path: str | Path | None = None,
    total_screened: int | None = None,
    total_failed: int | None = None,
    total_error: int | None = None,
) -> Path:
    """Generate a PDF report from screening results.

    Args:
        screening_results: List of dicts, each containing::

            {
                "screening": { ... screen_stock result ... },
                "fundamentals": { ... get_fundamentals result ... },
                "signals": { ... get_signals result ... },
            }

        output_path: Optional output file path. Defaults to
            ``~/halal-invest-reports/halal_report_YYYY-MM-DD.pdf``.
        total_screened: Override for total stocks screened count.
            If None, uses len(screening_results).
        total_failed: Override for failed count.
            If None, counts FAIL statuses in screening_results.
        total_error: Override for error count.
            If None, counts ERROR statuses in screening_results.

    Returns:
        The Path to the generated PDF file.
    """
    # Filter to only PASS and DOUBTFUL results
    passing_results = [
        r for r in screening_results
        if r.get("screening", {}).get("halal_status") in ("PASS", "DOUBTFUL")
    ]

    # Compute totals — use overrides if provided
    total_passed = len(passing_results)
    if total_screened is None:
        total_screened = len(screening_results)
    if total_failed is None:
        total_failed = sum(
            1 for r in screening_results
            if r.get("screening", {}).get("halal_status") == "FAIL"
        )
    if total_error is None:
        total_error = sum(
            1 for r in screening_results
            if r.get("screening", {}).get("halal_status") == "ERROR"
        )

    # Compute sector breakdown from passing stocks
    sector_breakdown: dict[str, int] = {}
    for r in passing_results:
        sector = r.get("screening", {}).get("sector", "Unknown")
        sector_breakdown[sector] = sector_breakdown.get(sector, 0) + 1

    # Build PDF
    pdf = HalalReportPDF()
    pdf.alias_nb_pages()

    # Summary
    pdf.add_summary_section(
        total_screened=total_screened,
        total_passed=total_passed,
        total_failed=total_failed,
        total_error=total_error,
        sector_breakdown=sector_breakdown,
    )

    # Individual stock sections
    for r in passing_results:
        screening = r.get("screening", {})
        fundamentals = r.get("fundamentals", {})
        signals = r.get("signals", {})

        stock_data = {
            "ticker": screening.get("ticker", "N/A"),
            "company": screening.get("company", "N/A"),
            "sector": screening.get("sector", "N/A"),
            "industry": screening.get("industry", "N/A"),
            "halal_screens": screening.get("screens", {}),
            "fundamentals": fundamentals,
            "signals": signals,
        }
        pdf.add_stock_section(stock_data)

    # Determine output path
    if output_path is None:
        today = datetime.now().strftime("%Y-%m-%d")
        output_dir = Path.home() / "halal-invest-reports"
        output_path = output_dir / f"halal_report_{today}.pdf"
    else:
        output_path = Path(output_path)

    # Create parent directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write PDF
    pdf.output(str(output_path))

    return output_path
