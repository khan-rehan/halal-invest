"""Send email with PDF attachment via Resend API."""

import os
import base64
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


RESEND_API_URL = "https://api.resend.com/emails"


def send_report_email(
    pdf_path: Path,
    total_screened: int,
    total_passed: int,
    recipient: str | None = None,
) -> bool:
    """Send the halal screening PDF report via Resend API.

    Credentials are read from environment variables:
    - RESEND_API_KEY: Resend API key
    - SENDER_EMAIL: verified sender email (e.g. reports@yourdomain.com or onboarding@resend.dev for testing)
    - RECIPIENT_EMAIL: recipient email address

    Returns True on success, False on failure.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
    recipient = recipient or os.environ.get("RECIPIENT_EMAIL")

    if not api_key:
        print("ERROR: RESEND_API_KEY environment variable must be set.")
        return False

    if not recipient:
        print("ERROR: No recipient email specified. Set RECIPIENT_EMAIL env var.")
        return False

    # Read and encode PDF as base64
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Build email body
    html_body = f"""
    <h2>Assalamu Alaikum,</h2>
    <p>Your daily Halal S&amp;P 500 screening report is attached.</p>
    <h3>Summary</h3>
    <ul>
        <li>Total S&amp;P 500 stocks screened: <strong>{total_screened}</strong></li>
        <li>Halal compliant (PASS): <strong>{total_passed}</strong></li>
        <li>Non-compliant (FAIL): <strong>{total_screened - total_passed}</strong></li>
    </ul>
    <p>The attached PDF contains detailed analysis of all passing stocks including:</p>
    <ul>
        <li>Halal screening ratios</li>
        <li>Valuation metrics (P/E, P/B, PEG)</li>
        <li>Profitability (margins, ROE, ROA)</li>
        <li>Growth (revenue &amp; earnings)</li>
        <li>Financial health (debt, cash flow)</li>
        <li>Technical signals (RSI, MACD, SMA, Bollinger)</li>
    </ul>
    <p>May your investments be blessed and profitable.</p>
    <p>— Halal Invest Tool</p>
    """

    # Build Resend API payload
    payload = {
        "from": sender,
        "to": [recipient],
        "subject": f"Halal S&P 500 Report — {total_passed} of {total_screened} stocks passed",
        "html": html_body,
        "attachments": [
            {
                "filename": pdf_path.name,
                "content": pdf_b64,
            }
        ],
    }

    # Send via Resend API
    try:
        req = Request(
            RESEND_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"Email sent successfully to {recipient} (ID: {result.get('id', 'N/A')})")
            return True
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        print(f"ERROR sending email (HTTP {e.code}): {error_body}")
        return False
    except URLError as e:
        print(f"ERROR sending email: {e.reason}")
        return False
    except Exception as e:
        print(f"ERROR sending email: {e}")
        return False
