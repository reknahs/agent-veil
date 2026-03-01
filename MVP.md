# MVP — 3-Person Architecture

## Current Status

### Cartographer (Live Graph & Dashboard) — DONE
- **components/AttackGraph.tsx** — React Force Graph, nodes turn red on breach
- **components/BreachFeed.tsx** — Live breach/log feed
- **convex/schema.ts** — breaches, logs, pr_status
- **convex/actions.ts** — launchAttack (demo), rebuildSecurity (calls fixer)
- **convex/httpActions.ts** — POST /api/log, POST /api/breach, GET /api/breaches
- **app/dashboard/page.tsx** — Launch Attack, Rebuild Security

### Person 3: Architect (Fixer & Sandbox) — DONE
- **fixer/repo_mapper.py** — Route → file path mapping
- **fixer/patch_engine.py** — Gemini 2.0 Flash for fixes
- **fixer/github_bot.py** — Branch, commit, open PR with evidence
- **fixer/sandbox_verify.py** — Daytona sandbox verification (optional)
- **fixer/api.py** — FastAPI: `POST /rebuild` runs pipeline

---

## How to Run

### 1. Convex + Next.js (required)

```bash
# Terminal 1: Convex dev
npx convex dev

# Terminal 2: Next.js
npm run dev
```

Set `.env.local`:
```
NEXT_PUBLIC_CONVEX_URL=https://YOUR-DEPLOYMENT.convex.cloud
```

### 2. Fixer API (optional — for real PRs)

```bash
pip install -r fixer/requirements.txt
# Set: GITHUB_TOKEN, GEMINI_API_KEY, CONVEX_SITE_URL
python -m fixer.api
```

Set Convex env `FIXER_API_URL=http://your-fixer-host:8001` so "Rebuild Security" creates real PRs.

---

## Flow

1. **Launch Attack** — Inserts sample breaches/logs → graph nodes turn red, feed updates.
2. **Rebuild Security** — Convex action fetches breaches → POSTs to fixer → fixer runs repo_mapper → patch_engine → github_bot → PR created.
