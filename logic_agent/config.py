"""Configuration for the GAN-like agent testing framework."""

import os
from dataclasses import dataclass
from typing import Optional

# Load .env (or .env.example if .env is missing)
try:
    from dotenv import load_dotenv
    from pathlib import Path
    _root = Path(__file__).resolve().parent.parent
    load_dotenv(_root / ".env")
    load_dotenv()
    if not os.environ.get("BROWSER_USE_API_KEY") and os.path.isfile(".env.example"):
        load_dotenv(".env.example")
except ImportError:
    pass

# Generic e-commerce description


# Generic e-commerce description when SITE_DESCRIPTION is not set (works for any site).
# Includes checkout, receipt, cart quantity, and pagination so bug-hunting workflows can be generated.
DEFAULT_SITE_DESCRIPTION = (
    "E-commerce site: navigation (Shop, categories), product listing (may have pagination with ?page=), "
    "product detail (click a product), add to cart, cart drawer or cart page with quantity inputs, "
    "checkout (shipping and payment forms, optional promo/gift card field), order/receipt confirmation page (URL often has orderId or similar). "
    "Only use features you can infer from the page. Do not assume search or filters unless visible."
)


@dataclass(frozen=True)
class Config:
    """Framework configuration. Prefer environment variables over defaults."""

    # Required (no defaults)
    browser_use_api_key: str
    minimax_api_key: str
    minimax_group_id: str
    target_url: str

    # Optional with defaults
    browser_use_base_url: str = "https://api.browser-use.com"
    minimax_base_url: str = "https://api.minimaxi.chat/v1"
    minimax_model: str = "minimax-text-01"
    allowed_domains: Optional[list[str]] = None
    site_description: str = ""
    system_prompt_extension: str = ""  # Extra instructions for the browser agent
    max_steps_per_task: int = 80
    poll_interval_seconds: float = 5.0
    workflows_per_round: int = 5
    max_rounds: int = 2

    @classmethod
    def from_env(
        cls,
        *,
        target_url: Optional[str] = None,
        allowed_domains: Optional[list[str]] = None,
        site_description: Optional[str] = None,
        system_prompt_extension: Optional[str] = None,
        workflows_per_round: int = 5,
        max_rounds: int = 2,
    ) -> "Config":
        """Build config from environment variables."""
        bu_key = os.environ.get("BROWSER_USE_API_KEY", "")
        mm_key = os.environ.get("MINIMAX_API_KEY", "")
        mm_group = os.environ.get("MINIMAX_GROUP_ID", "")
        mm_base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.chat/v1")
        mm_model = os.environ.get("MINIMAX_MODEL", "minimax-text-01")
        url = target_url or os.environ.get("TARGET_URL", "").strip() or "https://shanker.shopping/"
        url = url.rstrip("/")
        domains = allowed_domains
        if domains is None and url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            base_domain = f"{parsed.scheme}://{parsed.netloc}"
            domains = [base_domain, parsed.netloc]
        desc = site_description if site_description is not None else os.environ.get("SITE_DESCRIPTION", "").strip()
        if not desc:
            desc = DEFAULT_SITE_DESCRIPTION
        agent_instructions = system_prompt_extension if system_prompt_extension is not None else os.environ.get("AGENT_INSTRUCTIONS", "").strip()
        return cls(
            browser_use_api_key=bu_key,
            minimax_api_key=mm_key,
            minimax_group_id=mm_group,
            minimax_base_url=mm_base_url,
            minimax_model=mm_model,
            target_url=url,
            allowed_domains=domains,
            site_description=desc,
            system_prompt_extension=agent_instructions,
            workflows_per_round=workflows_per_round,
            max_rounds=max_rounds,
        )

    def validate(self) -> list[str]:
        """Return list of validation errors (empty if valid)."""
        errs = []
        if not self.browser_use_api_key:
            errs.append("BROWSER_USE_API_KEY is not set")
        if not self.minimax_api_key:
            errs.append("MINIMAX_API_KEY is not set")
        if not self.minimax_group_id:
            errs.append("MINIMAX_GROUP_ID is not set")
        if not self.target_url:
            errs.append("TARGET_URL is not set")
        return errs
