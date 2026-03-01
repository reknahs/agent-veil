"""
Agent main: FastAPI entry point that triggers the security agent
and sends results to Convex via HTTP actions.
"""

import os
import sys
from contextlib import asynccontextmanager

import uvicorn
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.playbooks import run_all_campaigns

CONVEX_SITE_URL = os.environ.get("CONVEX_SITE_URL", "https://unique-goshawk-48.convex.site")


def log_message(message: str, level: str = "info") -> None:
    """POST log to Convex."""
    try:
        resp = httpx.post(
            f"{CONVEX_SITE_URL}/api/log",
            json={"message": message, "level": level},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"[agent] log failed: {e}")


def report_breach(url: str, breach_type: str, screenshot_url: str | None = None) -> None:
    """POST breach to Convex."""
    try:
        payload = {"url": url, "type": breach_type}
        if screenshot_url:
            payload["screenshot_url"] = screenshot_url
        resp = httpx.post(
            f"{CONVEX_SITE_URL}/api/breach",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"[agent] breach report failed: {e}")


class RunRequest(BaseModel):
    target_url: str = "http://localhost:3000"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # cleanup if needed
    pass


app = FastAPI(title="Infiltrator Agent", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/run")
async def run_attack(req: RunRequest | None = None):
    """
    Run all 3 campaigns (Ghost Session, IDOR Hunter, Shields Up)
    against target_url and push logs/breaches to Convex.
    """
    target = (req or RunRequest()).target_url.rstrip("/")
    log_message(f"Starting security scan against {target}", "info")

    results = await run_all_campaigns(
        base_url=target,
        log_cb=log_message,
        breach_cb=report_breach,
    )

    breaches = [r for r in results if r[0]]
    log_message(f"Scan complete. {len(breaches)} breach(es) found.", "success" if breaches else "info")

    return {
        "ok": True,
        "target_url": target,
        "breaches_found": len(breaches),
        "results": [{"breach": r[0], "type": r[1], "url": r[2], "message": r[3]} for r in results],
    }


@app.get("/health")
def health():
    return {"ok": True, "convex_url": CONVEX_SITE_URL}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("agent.main:app", host="0.0.0.0", port=port, reload=False)
