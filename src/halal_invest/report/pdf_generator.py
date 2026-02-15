"""Generate PDF reports of SPUS halal investment analysis results."""

from datetime import datetime
from pathlib import Path
from fpdf import FPDF

from halal_invest.core.scoring import score_stock, get_valuation_tag, allocate_investment


class HalalReportPDF(FPDF):
    """Custom PDF document for SPUS halal investment reports."""

    # Color constants
    GREEN = (0, 128, 0)
    DARK_GREEN = (0, 80, 0)
    RED = (180, 30, 30)
    ORANGE = (200, 120, 0)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (128, 128, 128)
    LIGHT_GRAY = (240, 240, 240)
    HEADER_BG = (0, 128, 0)

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_font("Helvetica")

    # ------------------------------------------------------------------
    # Header / Footer
    # ------------------------------------------------------------------

    def header(self):
        """Draw page header with report title and date."""
        self.set_font("Helvetica", "B", 14)
        self.cell(
            0, 8, "SPUS Halal Investment Report",
            new_x="LMARGIN", new_y="NEXT", align="C",
        )
        self.set_font("Helvetica", "", 10)
        self.cell(
            0, 6, datetime.now().strftime("%A, %B %d, %Y"),
            new_x="LMARGIN", new_y="NEXT", align="C",
        )
        # Separator line
        self.set_draw_color(*self.GREEN)
        self.set_line_width(0.5)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        """Draw page footer with page numbers."""
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*self.GRAY)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", align="C")
        self.set_text_color(*self.BLACK)

    # ------------------------------------------------------------------
    # Page 1: Summary
    # ------------------------------------------------------------------

    def add_summary_section(
        self,
        total_stocks: int,
        avg_score: float,
        avg_cagr_5y: float | None,
        top_score: float,
        sector_breakdown: dict,
    ):
        """Add summary page with stat grid and sector breakdown."""
        # 4-box stat grid
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, "Analysis Overview", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        box_w = 45
        box_h = 18
        start_x = self.get_x()

        cagr_str = f"{avg_cagr_5y * 100:.1f}%" if avg_cagr_5y is not None else "N/A"

        stats = [
            ("Total SPUS Stocks", str(total_stocks)),
            ("Avg Score", f"{avg_score:.1f}"),
            ("Avg 5Y CAGR", cagr_str),
            ("Top Score", f"{top_score:.1f}"),
        ]

        for i, (label, value) in enumerate(stats):
            x = start_x + i * (box_w + 2)
            y = self.get_y()
            # Box border
            self.set_draw_color(180, 180, 180)
            self.set_line_width(0.3)
            self.rect(x, y, box_w, box_h)
            # Value (large)
            self.set_xy(x, y + 2)
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(*self.DARK_GREEN)
            self.cell(box_w, 8, value, align="C")
            # Label (small)
            self.set_xy(x, y + 10)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*self.GRAY)
            self.cell(box_w, 5, label, align="C")

        self.set_text_color(*self.BLACK)
        self.set_y(self.get_y() + box_h + 6)

        # Sector breakdown table
        if sector_breakdown:
            self.set_font("Helvetica", "B", 10)
            self.cell(
                0, 6, "Sector Breakdown (SPUS Holdings)",
                new_x="LMARGIN", new_y="NEXT",
            )
            self.ln(2)

            self._table_header_row(
                [("Sector", 80), ("Count", 30), ("% of Total", 40)],
            )

            sorted_sectors = sorted(
                sector_breakdown.items(), key=lambda x: x[1], reverse=True,
            )
            self.set_font("Helvetica", "", 9)

            for idx, (sector, count) in enumerate(sorted_sectors):
                pct = (count / total_stocks * 100) if total_stocks > 0 else 0.0
                self._set_row_bg(idx)
                self.cell(80, 5, self._sanitize(sector[:40]), border=1, fill=True)
                self.cell(30, 5, str(count), border=1, align="C", fill=True)
                self.cell(40, 5, f"{pct:.1f}%", border=1, align="C", fill=True)
                self.ln()

        self.ln(4)

    # ------------------------------------------------------------------
    # Page 2: Glossary / How to Read This Report
    # ------------------------------------------------------------------

    def add_glossary_page(self):
        """Add a reference page explaining every metric in simple English."""
        self.add_page()
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 8, "How to Read This Report", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        sections = [
            ("Valuation Metrics", [
                ("P/E (Price-to-Earnings)", "How many years of current earnings you're paying for the stock. Lower = cheaper. Under 15 is considered cheap, 15-25 is fair, over 25 is expensive."),
                ("P/B (Price-to-Book)", "Stock price relative to the company's net asset value. Under 1.5 is cheap, 1.5-3 is fair, over 3 is expensive."),
                ("PEG Ratio", "P/E adjusted for growth. Under 1 means growth exceeds the price you're paying -- a good sign."),
            ]),
            ("Profitability", [
                ("Net Margin", "How much profit the company keeps from each dollar of revenue. Higher is better."),
                ("ROE (Return on Equity)", "Profit generated per dollar of shareholder money. Measures how efficiently the company uses your investment."),
                ("ROA (Return on Assets)", "Profit generated per dollar of total assets. Shows overall efficiency."),
            ]),
            ("Growth", [
                ("Revenue Growth", "How fast the company's sales are increasing year-over-year."),
                ("Earnings Growth", "How fast profits are increasing. Strong earnings growth drives stock prices up."),
            ]),
            ("Historical Growth (CAGR)", [
                ("What is CAGR?", "Compound Annual Growth Rate -- the average yearly return if growth were perfectly smooth. A 10% CAGR over 5 years means $100 would become ~$161."),
                ("5Y CAGR", "Annualized stock price growth over the past 5 years. Shows medium-term momentum."),
                ("10Y CAGR", "Annualized stock price growth over the past 10 years. Shows long-term compounding ability."),
            ]),
            ("Financial Health", [
                ("Debt/Equity", "Total debt relative to shareholder equity. Lower means less financial risk."),
                ("Current Ratio", "Ability to pay short-term bills. Above 1.5 is healthy, below 1 is risky."),
                ("Free Cash Flow", "Cash left after expenses and investments. Positive FCF means the company generates real cash."),
            ]),
            ("Technical Signals", [
                ("RSI (Relative Strength Index)", "Measures if a stock is overbought (>70) or oversold (<30). Oversold = potential buy opportunity."),
                ("MACD", "Tracks momentum by comparing short-term vs long-term price trends. A crossover above the signal line suggests upward momentum."),
                ("SMA Crossover", "When the 50-day average crosses above the 200-day average (golden cross), it's bullish. Below = bearish."),
                ("Bollinger Bands", "Price bands around the average. Price near the lower band = potentially oversold and cheap."),
            ]),
            ("Composite Score (0-100)", [
                ("What it means", "A weighted score combining valuation (25%), profitability (20%), short-term growth (15%), historical growth (15%), financial health (15%), and technical signals (10%). Higher = better overall quality."),
            ]),
            ("Valuation Tag", [
                ("UNDERPRICED", "Stock appears cheap based on P/E, P/B, PEG, and 52-week position."),
                ("FAIR VALUE", "Stock is reasonably priced relative to its fundamentals."),
                ("OVERPRICED", "Stock appears expensive -- consider waiting for a dip."),
            ]),
        ]

        term_w = 45
        desc_w = 145

        for section_title, items in sections:
            if self.get_y() > 250:
                self.add_page()

            # Section header
            self.set_font("Helvetica", "B", 9)
            self.set_fill_color(*self.DARK_GREEN)
            self.set_text_color(*self.WHITE)
            self.cell(term_w + desc_w, 5, f"  {section_title}", border=1, fill=True)
            self.ln()
            self.set_text_color(*self.BLACK)

            for idx, (term, description) in enumerate(items):
                if self.get_y() > 265:
                    self.add_page()

                row_x = self.l_margin
                row_y = self.get_y()

                # Measure description height with multi_cell dry run
                self.set_font("Helvetica", "", 7)
                desc_lines = self.multi_cell(
                    desc_w - 2, 3.5, self._sanitize(description),
                    dry_run=True, output="LINES",
                )
                desc_h = max(len(desc_lines) * 3.5, 5)
                row_h = max(desc_h, 5)

                # Alternating row background
                if idx % 2 == 0:
                    self.set_fill_color(*self.LIGHT_GRAY)
                else:
                    self.set_fill_color(*self.WHITE)

                # Term cell (left column)
                self.set_xy(row_x, row_y)
                self.set_font("Helvetica", "B", 7)
                self.cell(term_w, row_h, self._sanitize(f" {term}"), border=1, fill=True)

                # Description cell (right column)
                self.set_xy(row_x + term_w, row_y)
                self.set_font("Helvetica", "", 7)
                # Draw the cell border and fill manually, then overlay text
                self.cell(desc_w, row_h, "", border=1, fill=True)
                self.set_xy(row_x + term_w + 1, row_y + 0.75)
                self.multi_cell(desc_w - 2, 3.5, self._sanitize(description))

                # Move to next row
                self.set_y(row_y + row_h)

            self.ln(2)

    # ------------------------------------------------------------------
    # Pages 3-4: Top 10 + Investment Plan
    # ------------------------------------------------------------------

    def add_top10_section(self, top10: list[dict], allocations: list[dict]):
        """Add Top 10 stocks and investment allocation plan.

        Args:
            top10: List of dicts with keys: rank, ticker, company,
                score, price, valuation_tag, cagr_5y, cagr_10y,
                pe_ratio, overall_signal.
            allocations: Output from ``allocate_investment()``.
        """
        self.add_page()
        self.set_font("Helvetica", "B", 13)
        self.cell(
            0, 8, "$1,000 Investment Plan + Top 10 Best Stocks",
            new_x="LMARGIN", new_y="NEXT",
        )
        self.ln(2)

        # --- Investment Allocation Table ---
        if allocations:
            self.set_font("Helvetica", "B", 10)
            self.cell(
                0, 6,
                "If you invest $1,000 today, here's how to distribute it:",
                new_x="LMARGIN", new_y="NEXT",
            )
            self.ln(2)

            col_widths = [15, 45, 25, 28, 30, 27]  # total = 170
            headers = ["#", "Company", "Price", "Valuation", "Allocation", "Shares"]
            self._table_header_row(list(zip(headers, col_widths)))

            self.set_font("Helvetica", "", 8)
            total_alloc = 0
            for i, a in enumerate(allocations):
                self._set_row_bg(i)
                self.cell(col_widths[0], 5, str(i + 1), border=1, align="C", fill=True)
                label = self._sanitize(f"{a['ticker']} - {a['company']}"[:28])
                self.cell(col_widths[1], 5, label, border=1, fill=True)
                self.cell(col_widths[2], 5, f"${a['price']:.2f}", border=1, align="R", fill=True)

                # Valuation tag - find from top10
                tag = ""
                for t in top10:
                    if t["ticker"] == a["ticker"]:
                        tag = t.get("valuation_tag", "")
                        break
                self._valuation_cell(tag, col_widths[3])

                self.cell(col_widths[4], 5, f"${a['allocation_dollars']:.0f}", border=1, align="R", fill=True)
                self.cell(col_widths[5], 5, f"{a['approx_shares']:.2f}", border=1, align="R", fill=True)
                self.ln()
                total_alloc += a["allocation_dollars"]

            # Total row
            self.set_font("Helvetica", "B", 8)
            self.set_fill_color(*self.LIGHT_GRAY)
            self.cell(col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3], 5, "TOTAL", border=1, align="R", fill=True)
            self.cell(col_widths[4], 5, f"${total_alloc:.0f}", border=1, align="R", fill=True)
            self.cell(col_widths[5], 5, "", border=1, fill=True)
            self.ln()

        self.ln(4)

        # --- Top 10 Ranked Table ---
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, "Top 10 SPUS Stocks by Composite Score", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        col_widths = [8, 14, 38, 14, 18, 24, 18, 18, 14, 18]  # 184 total
        headers = ["#", "Ticker", "Company", "Score", "Price", "Valuation", "5Y CAGR", "10Y CAGR", "P/E", "Signal"]
        self._table_header_row(list(zip(headers, col_widths)), font_size=7)

        self.set_font("Helvetica", "", 7)
        for i, stock in enumerate(top10):
            if self.get_y() > 265:
                self.add_page()
            self._set_row_bg(i)
            self.cell(col_widths[0], 5, str(i + 1), border=1, align="C", fill=True)
            self.cell(col_widths[1], 5, self._sanitize(stock.get("ticker", "")), border=1, fill=True)
            self.cell(col_widths[2], 5, self._sanitize(stock.get("company", "")[:24]), border=1, fill=True)

            # Score with color
            score = stock.get("score", 0)
            self._score_cell(score, col_widths[3])

            price = stock.get("price")
            price_str = f"${price:.2f}" if price else "N/A"
            self.cell(col_widths[4], 5, price_str, border=1, align="R", fill=True)

            self._valuation_cell(stock.get("valuation_tag", ""), col_widths[5])

            cagr_5y = stock.get("cagr_5y")
            cagr_5y_str = f"{cagr_5y * 100:.1f}%" if cagr_5y is not None else "N/A"
            self.cell(col_widths[6], 5, cagr_5y_str, border=1, align="R", fill=True)

            cagr_10y = stock.get("cagr_10y")
            cagr_10y_str = f"{cagr_10y * 100:.1f}%" if cagr_10y is not None else "N/A"
            self.cell(col_widths[7], 5, cagr_10y_str, border=1, align="R", fill=True)

            pe = stock.get("pe_ratio")
            self.cell(col_widths[8], 5, f"{pe:.1f}" if pe else "N/A", border=1, align="R", fill=True)

            signal = stock.get("overall_signal", "N/A")
            self._signal_cell(signal, col_widths[9])

            self.ln()

        self.ln(3)

        # Brief summary for each top 10 stock
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 5, "Quick Take on Each Pick:", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

        for i, stock in enumerate(top10):
            if self.get_y() > 268:
                self.add_page()
            ticker = stock.get("ticker", "")
            company = stock.get("company", "")
            score = stock.get("score", 0)
            tag = stock.get("valuation_tag", "FAIR VALUE")
            signal = stock.get("overall_signal", "HOLD")
            pe = stock.get("pe_ratio")
            cagr_5y = stock.get("cagr_5y")

            pe_note = f"P/E {pe:.1f}" if pe else "P/E N/A"
            cagr_note = f"5Y CAGR {cagr_5y * 100:.1f}%" if cagr_5y is not None else "5Y CAGR N/A"

            summary = f"{i+1}. {ticker} ({company}) -- Score {score}, {tag}, {signal} signal, {pe_note}, {cagr_note}"
            self.set_font("Helvetica", "", 7)
            self.set_x(self.l_margin)
            self.multi_cell(190, 3.5, self._sanitize(summary))

    # ------------------------------------------------------------------
    # All Stocks: Compact Table grouped by Sector
    # ------------------------------------------------------------------

    def add_all_stocks_section(self, stocks_by_sector: dict):
        """Add compact tables of all stocks grouped by sector.

        Args:
            stocks_by_sector: Dict mapping sector name to list of stock dicts.
                Each stock dict has: ticker, company, score, price,
                valuation_tag, cagr_5y, cagr_10y, pe_ratio, roe,
                revenue_growth, overall_signal.
        """
        self.add_page()
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 8, "All SPUS Holdings", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        col_widths = [15, 34, 14, 18, 24, 16, 16, 15, 16, 16]  # 184 total
        headers = ["Ticker", "Company", "Score", "Price", "Valuation", "5Y CAGR", "10Y CAGR", "P/E", "Growth", "Signal"]

        sorted_sectors = sorted(stocks_by_sector.keys())

        for sector in sorted_sectors:
            stocks = stocks_by_sector[sector]
            if not stocks:
                continue

            # Sector header
            if self.get_y() > 250:
                self.add_page()

            self.set_font("Helvetica", "B", 9)
            self.set_fill_color(*self.GREEN)
            self.set_text_color(*self.WHITE)
            total_w = sum(col_widths)
            self.cell(total_w, 6, self._sanitize(f"  {sector} ({len(stocks)} stocks)"), border=1, fill=True)
            self.ln()
            self.set_text_color(*self.BLACK)

            # Column headers
            self._table_header_row(
                list(zip(headers, col_widths)),
                font_size=7,
                bg_color=(60, 60, 60),
            )

            self.set_font("Helvetica", "", 7)
            for idx, stock in enumerate(stocks):
                if self.get_y() > 272:
                    self.add_page()
                    # Re-print sector continuation header
                    self.set_font("Helvetica", "B", 8)
                    self.set_fill_color(*self.GREEN)
                    self.set_text_color(*self.WHITE)
                    self.cell(total_w, 5, self._sanitize(f"  {sector} (cont.)"), border=1, fill=True)
                    self.ln()
                    self.set_text_color(*self.BLACK)
                    self._table_header_row(
                        list(zip(headers, col_widths)),
                        font_size=7,
                        bg_color=(60, 60, 60),
                    )
                    self.set_font("Helvetica", "", 7)

                self._set_row_bg(idx)

                self.cell(col_widths[0], 4.5, self._sanitize(stock.get("ticker", "")), border=1, fill=True)
                self.cell(col_widths[1], 4.5, self._sanitize(stock.get("company", "")[:20]), border=1, fill=True)

                self._score_cell(stock.get("score", 0), col_widths[2], height=4.5)

                price = stock.get("price")
                price_str = f"${price:.0f}" if price else "N/A"
                self.cell(col_widths[3], 4.5, price_str, border=1, align="R", fill=True)

                self._valuation_cell(stock.get("valuation_tag", ""), col_widths[4], height=4.5)

                cagr_5y = stock.get("cagr_5y")
                cagr_5y_str = f"{cagr_5y * 100:.1f}%" if cagr_5y is not None else "N/A"
                self.cell(col_widths[5], 4.5, cagr_5y_str, border=1, align="R", fill=True)

                cagr_10y = stock.get("cagr_10y")
                cagr_10y_str = f"{cagr_10y * 100:.1f}%" if cagr_10y is not None else "N/A"
                self.cell(col_widths[6], 4.5, cagr_10y_str, border=1, align="R", fill=True)

                pe = stock.get("pe_ratio")
                self.cell(col_widths[7], 4.5, f"{pe:.1f}" if pe else "N/A", border=1, align="R", fill=True)

                growth = stock.get("revenue_growth")
                growth_str = self._format_value(growth, "pct") if growth is not None else "N/A"
                self.cell(col_widths[8], 4.5, growth_str, border=1, align="R", fill=True)

                self._signal_cell(stock.get("overall_signal", "N/A"), col_widths[9], height=4.5)

                self.ln()

            self.ln(2)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _table_header_row(self, columns: list[tuple[str, float]], font_size: int = 8, bg_color: tuple = None):
        """Draw a table header row with green background.

        Args:
            columns: List of (header_text, width) tuples.
            font_size: Font size for header text.
            bg_color: Optional RGB tuple. Defaults to HEADER_BG.
        """
        bg = bg_color or self.HEADER_BG
        self.set_font("Helvetica", "B", font_size)
        self.set_fill_color(*bg)
        self.set_text_color(*self.WHITE)
        for text, width in columns:
            self.cell(width, 5, text, border=1, align="C", fill=True)
        self.ln()
        self.set_text_color(*self.BLACK)

    def _set_row_bg(self, idx: int):
        """Set alternating row background color."""
        if idx % 2 == 0:
            self.set_fill_color(*self.LIGHT_GRAY)
        else:
            self.set_fill_color(*self.WHITE)

    def _valuation_cell(self, tag: str, width: float, height: float = 5):
        """Render a valuation tag cell with color coding."""
        if tag == "UNDERPRICED":
            self.set_text_color(*self.GREEN)
        elif tag == "OVERPRICED":
            self.set_text_color(*self.RED)
        elif tag == "FAIR VALUE":
            self.set_text_color(*self.ORANGE)
        else:
            self.set_text_color(*self.BLACK)

        self.set_font("Helvetica", "B", 6)
        self.cell(width, height, tag, border=1, align="C", fill=True)
        self.set_text_color(*self.BLACK)
        self.set_font("Helvetica", "", 7)

    def _score_cell(self, score: float, width: float, height: float = 5):
        """Render a score cell with color based on value."""
        if score >= 70:
            self.set_text_color(*self.GREEN)
        elif score >= 50:
            self.set_text_color(*self.ORANGE)
        else:
            self.set_text_color(*self.RED)

        self.set_font("Helvetica", "B", 7)
        self.cell(width, height, f"{score:.0f}", border=1, align="C", fill=True)
        self.set_text_color(*self.BLACK)
        self.set_font("Helvetica", "", 7)

    def _signal_cell(self, signal: str, width: float, height: float = 5):
        """Render a technical signal cell with color."""
        sig = (signal or "N/A").upper()
        if sig == "BUY":
            self.set_text_color(*self.GREEN)
        elif sig == "SELL":
            self.set_text_color(*self.RED)
        else:
            self.set_text_color(*self.GRAY)

        self.set_font("Helvetica", "B", 7)
        self.cell(width, height, sig, border=1, align="C", fill=True)
        self.set_text_color(*self.BLACK)
        self.set_font("Helvetica", "", 7)

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
        return text.encode("latin-1", errors="replace").decode("latin-1")

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
    stock_results: list[dict],
    output_path: str | Path | None = None,
) -> Path:
    """Generate a PDF report from SPUS stock analysis results.

    Args:
        stock_results: List of dicts, each containing::

            {
                "ticker": "AAPL",
                "fundamentals": { ... get_fundamentals result ... },
                "signals": { ... get_signals result ... },
                "historical_growth": { ... get_historical_growth result ... },
            }

        output_path: Optional output file path. Defaults to
            ``~/halal-invest-reports/spus_report_YYYY-MM-DD.pdf``.

    Returns:
        The Path to the generated PDF file.
    """
    # Compute sector breakdown
    sector_breakdown: dict[str, int] = {}
    for r in stock_results:
        sector = r.get("fundamentals", {}).get("sector") or "Unknown"
        sector_breakdown[sector] = sector_breakdown.get(sector, 0) + 1

    # Score and tag every stock
    scored_stocks = []
    for r in stock_results:
        fundamentals = r.get("fundamentals", {})
        signals = r.get("signals", {})
        historical_growth = r.get("historical_growth", {})

        composite_score = score_stock(fundamentals, signals, historical_growth)
        valuation_tag = get_valuation_tag(fundamentals)

        scored_stocks.append({
            "ticker": r.get("ticker", "N/A"),
            "company": fundamentals.get("name") or "N/A",
            "sector": fundamentals.get("sector") or "N/A",
            "industry": fundamentals.get("industry") or "N/A",
            "score": composite_score,
            "valuation_tag": valuation_tag,
            "price": fundamentals.get("current_price"),
            "pe_ratio": fundamentals.get("pe_ratio"),
            "roe": fundamentals.get("roe"),
            "revenue_growth": fundamentals.get("revenue_growth"),
            "overall_signal": signals.get("overall", {}).get("signal", "N/A"),
            "cagr_5y": historical_growth.get("cagr_5y"),
            "cagr_10y": historical_growth.get("cagr_10y"),
        })

    # Sort by score descending
    scored_stocks.sort(key=lambda s: s["score"], reverse=True)

    # Compute summary stats
    total_stocks = len(scored_stocks)
    avg_score = sum(s["score"] for s in scored_stocks) / total_stocks if total_stocks else 0
    top_score = scored_stocks[0]["score"] if scored_stocks else 0

    cagr_5y_values = [s["cagr_5y"] for s in scored_stocks if s["cagr_5y"] is not None]
    avg_cagr_5y = sum(cagr_5y_values) / len(cagr_5y_values) if cagr_5y_values else None

    # Top 10
    top10 = scored_stocks[:10]

    # Investment allocation
    allocations = allocate_investment(top10)

    # Group all stocks by sector
    stocks_by_sector: dict[str, list[dict]] = {}
    for stock in scored_stocks:
        sector = stock["sector"]
        stocks_by_sector.setdefault(sector, []).append(stock)
    # Sort stocks within each sector by score
    for sector in stocks_by_sector:
        stocks_by_sector[sector].sort(key=lambda s: s["score"], reverse=True)

    # Build PDF
    pdf = HalalReportPDF()
    pdf.add_page()
    pdf.alias_nb_pages()

    # Page 1: Summary
    pdf.add_summary_section(
        total_stocks=total_stocks,
        avg_score=avg_score,
        avg_cagr_5y=avg_cagr_5y,
        top_score=top_score,
        sector_breakdown=sector_breakdown,
    )

    # Page 2: Glossary
    pdf.add_glossary_page()

    # Pages 3-4: Top 10 + Investment Plan
    pdf.add_top10_section(top10, allocations)

    # Remaining pages: All stocks
    pdf.add_all_stocks_section(stocks_by_sector)

    # Determine output path
    if output_path is None:
        today = datetime.now().strftime("%Y-%m-%d")
        output_dir = Path.home() / "halal-invest-reports"
        output_path = output_dir / f"spus_report_{today}.pdf"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))

    return output_path
