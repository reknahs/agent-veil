# MVP — 3-Person Architecture

## Current Status

### Person 1: Infiltrator (Agent & Telemetry) — DONE
- **agent/playbooks.py** — 3 campaigns: Ghost Session, IDOR Hunter, Shields Up
- **agent/telemetry.py** — Intercepts `page.on("response")` and `page.on("console")` for 401/403/500 and JS errors
- **agent/main.py** — FastAPI entry point: `POST /run` triggers agent and sends results to Convex

### Person 2: Cartographer (Live Graph & Dashboard) — DONE
- **components/AttackGraph.tsx** — React Force Graph, nodes turn red on breach
- **components/BreachFeed.tsx** — Live agent thoughts log
- **convex/schema.ts** — breaches, logs, pr_status
- **convex/actions.ts** — launchAttack (demo + real agent), rebuildSecurity (calls fixer)
- **convex/httpActions.ts** — POST /api/log, POST /api/breach, GET /api/breaches
- **app/dashboard/page.tsx** — Launch Attack (Demo), Launch Real Attack, Rebuild Security

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

### 2. Infiltrator Agent (optional — for real attacks)

```bash
cd agent
pip install -r requirements.txt
playwright install chromium
CONVEX_SITE_URL=https://YOUR-DEPLOYMENT.convex.site python main.py
```

Set Convex env `AGENT_API_URL=http://your-agent-host:8000` to trigger real agent from "Launch Real Attack".

### 3. Fixer API (optional — for real PRs)

```bash
pip install -r fixer/requirements.txt
# Set: GITHUB_TOKEN, GEMINI_API_KEY, CONVEX_SITE_URL
python -m fixer.api
```

Set Convex env `FIXER_API_URL=http://your-fixer-host:8001` so "Rebuild Security" creates real PRs.

---

## Flow

1. **Launch Attack (Demo)** — Inserts sample breaches/logs → graph nodes turn red, feed updates.
2. **Launch Real Attack** — Calls agent API → agent runs 3 campaigns → POSTs to Convex → same UI.
3. **Rebuild Security** — Convex action fetches breaches → POSTs to fixer → fixer runs repo_mapper → patch_engine → github_bot → PR created.
