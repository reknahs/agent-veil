# Fixer (Architect)

Remediation and code-level logic: map routes to files, generate fixes with Gemini, open PRs via GitHub API, verify builds in a Daytona sandbox.

## Quick test (no API keys)

From the **repo root** (`ycombinator-hackathon`):

**Option A – no extra deps (recommended first):**
```bash
python3 fixer/run_tests.py
```
This runs repo_mapper, patch_engine helpers, and token/key checks for GitHub and Daytona. No `pip install` needed if you have the fixer deps already; otherwise install with Option B first.

**Option B – full test suite with pytest:**
```bash
pip install -r fixer/requirements.txt
pytest fixer/tests -v
```

Tests cover:
- **repo_mapper**: route → file candidates and resolving to existing files
- **patch_engine**: code-block extraction and `apply_fix_to_content`
- **github_bot** / **sandbox_verify**: error messages when tokens/keys are missing

## Test with real APIs

Set the env vars for the parts you want to try, then run the same tests or call the modules from Python.

| Component      | Env vars              | What to run |
|----------------|------------------------|-------------|
| **repo_mapper** | none                   | `pytest fixer/tests/test_repo_mapper.py -v` (no keys) |
| **patch_engine** | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | In Python: `from fixer.patch_engine import generate_fix; generate_fix("Error: x is undefined", "const x = 1;", "app/page.tsx")` |
| **github_bot**  | `GITHUB_TOKEN` or `GH_TOKEN` | In Python: use `create_fix_pr(...)` against a real repo you can push to |
| **sandbox_verify** | `DAYTONA_API_KEY` | In Python: `from fixer.sandbox_verify import verify_build; verify_build("https://github.com/...", "npm run build")` |

## One-liner smoke (repo root)

```bash
cd /Users/vibha/Downloads/ycombinator-hackathon
pip install -r fixer/requirements.txt pytest
pytest fixer/tests -v
```
