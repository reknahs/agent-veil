"""
Telemetry: Intercepts Playwright page.on("response") and page.on("console")
to catch 401/403 errors, 500 crashes, and JS stack traces.
Sends findings to Convex via HTTP actions.
"""

import asyncio
from typing import Callable, Optional
from playwright.async_api import Page, Response, ConsoleMessage

# Callbacks to send logs and breaches to Convex
_log_cb: Optional[Callable[[str, str], None]] = None
_breach_cb: Optional[Callable[[str, str, Optional[str]], None]] = None


def set_callbacks(
    log_cb: Callable[[str, str], None],
    breach_cb: Callable[[str, str, Optional[str]], None],
) -> None:
    """Set callbacks for log and breach reporting (called from main.py)."""
    global _log_cb, _breach_cb
    _log_cb = log_cb
    _breach_cb = breach_cb


def _log(message: str, level: str = "info") -> None:
    if _log_cb:
        _log_cb(message, level)


def _report_breach(url: str, breach_type: str, screenshot_url: Optional[str] = None) -> None:
    if _breach_cb:
        _breach_cb(url, breach_type, screenshot_url)


async def attach_telemetry(page: Page) -> None:
    """
    Attach response and console listeners to a Playwright page.
    Catches 401/403/500 responses and JS errors, reports as logs/breaches.
    """

    async def on_response(response: Response) -> None:
        url = response.url
        status = response.status
        if status in (401, 403):
            _log(f"Auth error {status} on {url}", "warn")
            # Could report as Auth Bypass / Cookie Leaks depending on context
            _report_breach(url, "Auth Bypass")
        elif status >= 500:
            _log(f"Server error {status} on {url}", "error")
            _report_breach(url, "Server Error")

    async def on_console(msg: ConsoleMessage) -> None:
        text = msg.text
        _type = msg.type
        if _type == "error":
            _log(f"Console error: {text}", "error")
            # If it looks like a stack trace or security-related, could report
            if "401" in text or "403" in text or "unauthorized" in text.lower():
                loc = msg.location
                url = loc.get("url", "") if loc else ""
                if url:
                    _report_breach(url, "Cookie Leaks")

    page.on("response", on_response)
    page.on("console", on_console)
