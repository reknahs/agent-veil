"""
reporting.py — Send live logs and breach reports to the Convex dashboard.

If CONVEX_SITE_URL is not set, calls are no-ops (allows standalone CLI usage).
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

CONVEX_SITE_URL = os.getenv("CONVEX_SITE_URL", "")


def log_message(message: str, level: str = "info") -> None:
    """Post an agent-thought entry to the Breach Feed."""
    if not CONVEX_SITE_URL:
        return
    try:
        requests.post(
            f"{CONVEX_SITE_URL}/api/log",
            json={"message": message, "level": level},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
    except requests.RequestException:
        pass


def report_breach(url: str, breach_type: str, screenshot_url: str | None = None) -> None:
    """Record a confirmed breach so the Attack Graph node turns red."""
    if not CONVEX_SITE_URL:
        return
    payload: dict = {"url": url, "type": breach_type}
    if screenshot_url:
        payload["screenshot_url"] = screenshot_url
    try:
        requests.post(
            f"{CONVEX_SITE_URL}/api/breach",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
    except requests.RequestException:
        pass
