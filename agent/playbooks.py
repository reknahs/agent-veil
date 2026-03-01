"""
Playbooks: Defines logic for 3 security campaigns.
- Ghost Session: Log out, hit Back, check if sensitive data persists in DOM
- IDOR Hunter: Navigate to user profile, try id=101 -> id=102
- Shields Up: Check for missing CSP, X-Frame-Options headers
"""

import asyncio
from typing import Optional
from playwright.async_api import Page, async_playwright

from agent.telemetry import attach_telemetry


# Campaign results: (breach_found, breach_type, url, message)
CampaignResult = tuple[bool, Optional[str], str, str]


async def run_ghost_session(
    page: Page,
    base_url: str,
    login_url: str = "/",
    logout_selector: str = 'button:has-text("Sign Out"), a:has-text("Sign Out"), [data-testid="logout"]',
) -> CampaignResult:
    """
    Ghost Session: Log out, hit Back, see if sensitive data persists.
    If we still see user data after logout + back, it's Auth Bypass.
    """
    try:
        await page.goto(base_url + login_url, wait_until="domcontentloaded", timeout=10000)
        await asyncio.sleep(0.5)

        # Try to find and click logout
        logout = page.locator(logout_selector).first
        if await logout.count() > 0:
            await logout.click()
            await asyncio.sleep(0.5)

        # Hit back
        await page.go_back(wait_until="domcontentloaded", timeout=5000)
        await asyncio.sleep(0.5)

        content = await page.content()
        # Heuristic: if we see common "authenticated" markers after logout+back
        auth_markers = ["Welcome", "Dashboard", "Settings", "user@", "logout", "Logout", "Profile"]
        found = [m for m in auth_markers if m.lower() in content.lower()]
        if len(found) >= 2:
            return True, "Auth Bypass", page.url, f"Ghost Session: sensitive data persisted after logout (found: {found})"
        return False, None, page.url, "Ghost Session: no obvious data leak after logout+back"
    except Exception as e:
        return False, None, page.url, f"Ghost Session: {type(e).__name__}: {e}"


async def run_idor_hunter(
    page: Page,
    base_url: str,
    profile_path: str = "/api/user",
    id_param: str = "id",
    test_ids: tuple[int, int] = (101, 102),
) -> CampaignResult:
    """
    IDOR Hunter: Try changing id=101 to id=102 in URL.
    If we get 200 with different user's data, it's IDOR.
    """
    try:
        url1 = f"{base_url}{profile_path}?{id_param}={test_ids[0]}"
        await page.goto(url1, wait_until="domcontentloaded", timeout=10000)
        await asyncio.sleep(0.3)
        content1 = (await page.content())[:2000]

        url2 = f"{base_url}{profile_path}?{id_param}={test_ids[1]}"
        await page.goto(url2, wait_until="domcontentloaded", timeout=10000)
        await asyncio.sleep(0.3)
        content2 = (await page.content())[:2000]

        # Heuristic: if both return 200 and content differs (we accessed another user's data)
        status2 = await page.evaluate("() => document.body?.innerText?.length ?? 0")
        if content1 != content2 and len(content2) > 50:
            return True, "IDOR", url2, f"IDOR: different response for {id_param}={test_ids[1]} (possible data leak)"
        return False, None, url2, f"IDOR Hunter: no obvious IDOR for {id_param}={test_ids[1]}"
    except Exception as e:
        return False, None, page.url if page.url else profile_path, f"IDOR Hunter: {type(e).__name__}: {e}"


async def run_shields_up(
    page: Page,
    base_url: str,
    path: str = "/",
) -> CampaignResult:
    """
    Shields Up: Check for missing CSP, X-Frame-Options headers.
    """
    missing_headers: list[str] = []
    try:
        response = await page.goto(base_url + path, wait_until="domcontentloaded", timeout=10000)
        if response:
            headers = response.headers
            if not headers.get("content-security-policy") and not headers.get("x-webkit-csp"):
                missing_headers.append("Content-Security-Policy")
            if not headers.get("x-frame-options"):
                missing_headers.append("X-Frame-Options")
            if not headers.get("x-content-type-options"):
                missing_headers.append("X-Content-Type-Options")
        if missing_headers:
            return True, "Missing Headers", base_url + path, f"Shields Up: missing headers {missing_headers}"
        return False, None, base_url + path, "Shields Up: key security headers present"
    except Exception as e:
        return False, None, base_url + path, f"Shields Up: {type(e).__name__}: {e}"


async def run_all_campaigns(
    base_url: str,
    log_cb,
    breach_cb,
) -> list[CampaignResult]:
    """
    Run all 3 campaigns and report via callbacks.
    Returns list of (breach_found, breach_type, url, message) for each.
    """
    from agent.telemetry import set_callbacks
    set_callbacks(log_cb, breach_cb)

    results: list[CampaignResult] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()
            await attach_telemetry(page)

            # Ghost Session
            log_cb("Running Ghost Session (logout + back)...", "info")
            r1 = await run_ghost_session(page, base_url)
            results.append(r1)
            if r1[0]:
                log_cb(r1[3], "success")
                breach_cb(r1[2], r1[1], None)
            else:
                log_cb(r1[3], "info")

            # IDOR Hunter
            log_cb("Running IDOR Hunter (/api/user id=101 -> 102)...", "info")
            r2 = await run_idor_hunter(page, base_url, profile_path="/api/user")
            results.append(r2)
            if r2[0]:
                log_cb(r2[3], "success")
                breach_cb(r2[2], r2[1], None)
            else:
                log_cb(r2[3], "info")

            # Shields Up
            log_cb("Running Shields Up (security headers)...", "info")
            r3 = await run_shields_up(page, base_url)
            results.append(r3)
            if r3[0]:
                log_cb(r3[3], "success")
                breach_cb(r3[2], r3[1], None)
            else:
                log_cb(r3[3], "info")

        finally:
            await browser.close()

    return results
