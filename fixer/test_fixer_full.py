"""
Unified verification script for Fixer components.
Tests Repo Mapper, GitHub Bot (requests-based), and API Health.
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from fixer.repo_mapper import route_to_file_candidates
from fixer.github_bot import _get_headers, get_file_content

def test_repo_mapper():
    print("\n--- Testing Repo Mapper ---")
    candidates = route_to_file_candidates("/admin")
    print(f"Route '/admin' candidates: {candidates}")
    assert "app/admin/page.tsx" in candidates or "src/app/admin/page.tsx" in candidates
    print("✅ Repo Mapper OK")

def test_github_bot_auth():
    print("\n--- Testing GitHub Bot Auth ---")
    try:
        headers = _get_headers()
        print("✅ Headers generated (Token found)")
    except Exception as e:
        print(f"❌ Auth Failed: {e}")
        return False
    return True

def test_github_repo_access():
    print("\n--- Testing GitHub Repo Access ---")
    repo = "reknahs/e-commerce-website-build"
    headers = _get_headers()
    url = f"https://api.github.com/repos/{repo}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        print(f"✅ Repo '{repo}' is accessible.")
        # Try fetching a file
        content = get_file_content(repo, "README.md", "main")
        if content:
            print(f"✅ Successfully fetched README.md ({len(content)} bytes)")
        else:
            # Try 'master' if 'main' fails
            content = get_file_content(repo, "README.md", "master")
            if content:
                print(f"✅ Successfully fetched README.md from 'master' ({len(content)} bytes)")
            else:
                print("⚠️ Could not fetch README.md (Check branch name)")
    else:
        print(f"❌ Repo access failed: {r.status_code} {r.text}")

def test_api_health():
    print("\n--- Testing API Health ---")
    try:
        r = requests.get("http://localhost:8001/health", timeout=5)
        if r.status_code == 200:
            print("✅ Fixer API is alive at :8001")
        else:
            print(f"❌ API returned {r.status_code}")
    except Exception as e:
        print(f"⚠️ API not reachable (is it running?): {e}")

if __name__ == "__main__":
    test_repo_mapper()
    if test_github_bot_auth():
        test_github_repo_access()
    test_api_health()
