"""Send email with PDF attachment via Gmail SMTP."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path


def send_report_email(
    pdf_path: Path,
    total_screened: int,
    total_passed: int,
    recipient: str | None = None,
) -> bool:
    """Send the halal screening PDF report via Gmail SMTP.

    Credentials are read from environment variables:
    - GMAIL_ADDRESS: sender email
    - GMAIL_APP_PASSWORD: Gmail app password
    - RECIPIENT_EMAIL: recipient (can be overridden by parameter)

    Returns True on success, False on failure.
    """
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = recipient or os.environ.get("RECIPIENT_EMAIL", gmail_address)

    if not gmail_address or not gmail_password:
        print("ERROR: GMAIL_ADDRESS and GMAIL_APP_PASSWORD environment variables must be set.")
        return False

    if not recipient:
        print("ERROR: No recipient email specified.")
        return False

    # Build email
    msg = MIMEMultipart()
    msg["From"] = gmail_address
    msg["To"] = recipient
    msg["Subject"] = f"Halal S&P 500 Report — {total_passed} of {total_screened} stocks passed"

    body = f"""Assalamu Alaikum,

Your daily Halal S&P 500 screening report is attached.

Summary:
- Total S&P 500 stocks screened: {total_screened}
- Halal compliant (PASS): {total_passed}
- Non-compliant (FAIL): {total_screened - total_passed}

The attached PDF contains detailed analysis of all passing stocks including:
- Halal screening ratios
- Valuation metrics (P/E, P/B, PEG)
- Profitability (margins, ROE, ROA)
- Growth (revenue & earnings)
- Financial health (debt, cash flow)
- Technical signals (RSI, MACD, SMA, Bollinger)

May your investments be blessed and profitable.

— Halal Invest Tool
"""
    msg.attach(MIMEText(body, "plain"))

    # Attach PDF
    with open(pdf_path, "rb") as f:
        pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
        pdf_attachment.add_header(
            "Content-Disposition", "attachment",
            filename=pdf_path.name,
        )
        msg.attach(pdf_attachment)

    # Send via Gmail SMTP
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_address, gmail_password)
            server.send_message(msg)
        print(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        print(f"ERROR sending email: {e}")
        return False
