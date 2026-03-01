# Setup Guide

## Fix "ArgumentValidationError: Object contains extra field 'target_url'"

Your Convex deployment may be out of sync. Push the latest schema:

```bash
npx convex dev
```

Leave this running in a separate terminal. It syncs your Convex functions and schema.

---

## API Keys

| Feature | API Keys | Where |
|---------|----------|-------|
| **Demo mode** | None | Works out of the box |
| **Launch Real Attack** | None | Agent needs `CONVEX_SITE_URL` (Convex site URL) |
| **Rebuild Security (real PRs)** | `GITHUB_TOKEN`, `GEMINI_API_KEY` | Set in fixer env when running `python -m fixer.api` |

### For Real Agent (Launch Real Attack)
1. Run the agent: `cd agent && pip install -r requirements.txt && playwright install chromium && python main.py`
2. Set in Convex dashboard: `AGENT_API_URL=http://localhost:8000`

### For Real Fixer (Rebuild Security → actual GitHub PR)
1. Create a [GitHub Personal Access Token](https://github.com/settings/tokens) with `repo` scope
2. Get a [Gemini API key](https://ai.google.dev/)
3. Run the fixer: `GITHUB_TOKEN=ghp_xxx GEMINI_API_KEY=xxx python -m fixer.api`
4. Set in Convex dashboard: `FIXER_API_URL=http://localhost:8001`
5. Enter the GitHub repo in the dashboard (e.g. `jayadevgh/jayadevgh.github.io`) before clicking Rebuild Security
