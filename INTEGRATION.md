# Integration Guide for Person 1 (Infiltrator Agent)

This document explains how the Infiltrator agent sends breach reports and logs to Convex so the Cartographer dashboard displays them in real time.

## HTTP Actions Base URL

```
https://unique-goshawk-48.convex.site
```

In Convex functions, this is available as `process.env.CONVEX_SITE_URL`.

---

## Endpoints for the Agent

### POST `/api/log`

Appends an "agent thought" entry to the live Breach Feed.

**Request:**
```
POST https://unique-goshawk-48.convex.site/api/log
Content-Type: application/json

{
  "message": "Attempting IDOR on /api/user... Success.",
  "level": "success"   // optional: "info" | "success" | "warn" | "error"
}
```

**Response:** `{ "ok": true }` (200) or `{ "error": "..." }` (400/500)

---

### POST `/api/breach`

Records a confirmed security breach. Nodes for that URL turn **red** on the Attack Graph.

**Request:**
```
POST https://unique-goshawk-48.convex.site/api/breach
Content-Type: application/json

{
  "url": "/api/user",
  "type": "IDOR",
  "screenshot_url": "https://..."   // optional
}
```

**Supported breach types (examples):**
- `Auth Bypass` — Ghost Session, etc.
- `IDOR` — IDOR Hunter findings
- `Cookie Leaks` — Shields Up / cookie issues

**Response:** `{ "ok": true }` (200) or `{ "error": "..." }` (400/500)

---

## Python Example (Person 1’s `agent/main.py`)

```python
import requests

CONVEX_SITE_URL = "https://unique-goshawk-48.convex.site"

def log_message(message: str, level: str = "info"):
    requests.post(
        f"{CONVEX_SITE_URL}/api/log",
        json={"message": message, "level": level},
        headers={"Content-Type": "application/json"},
    )

def report_breach(url: str, breach_type: str, screenshot_url: str | None = None):
    payload = {"url": url, "type": breach_type}
    if screenshot_url:
        payload["screenshot_url"] = screenshot_url
    requests.post(
        f"{CONVEX_SITE_URL}/api/breach",
        json=payload,
        headers={"Content-Type": "application/json"},
    )

# Usage during a campaign:
log_message("Attempting IDOR on /api/user...", "info")
# ... run test ...
log_message("Attempting IDOR on /api/user... Success.", "success")
report_breach("/api/user", "IDOR")
```

---

## Launch Attack Integration

**Current behavior:** The "Launch Attack" button runs a **demo** that inserts sample logs and breaches. It does not start the real agent.

**When Person 1’s agent is ready:**

- **Option A — Agent started from dashboard:** "Launch Attack" calls Person 1’s API (e.g. `POST https://agent-api/start`). The agent runs and pushes logs/breaches to Convex via the HTTP actions above. The dashboard already reacts to Convex updates.
- **Option B — Agent run separately:** Person 1 runs the agent (e.g. `python agent/main.py`). It posts logs and breaches to Convex. "Launch Attack" can remain a demo or be repurposed.

---

## Schema Reference (Convex)

- **`logs`:** `{ timestamp, message, level? }`
- **`breaches`:** `{ url, type, screenshot_url?, confirmedAt }`
- **`pr_status`:** Used by "Rebuild Security" for the fix PR flow.
