# MVP — Current Architecture

## Cartographer (Dashboard)

- **app/dashboard/page.tsx** — Website URL + GitHub repo inputs, **Analyze** button. Calls agent API (direct or via Next.js proxy). Displays findings as cards (title, summary, expandable details).
- **app/api/run-scan/route.ts** — Proxies `POST /api/run-scan` to the agent (avoids CORS).
- **app/api/run-scan/stream/route.ts** — Proxies `POST /api/run-scan/stream` for SSE streaming.
- **components/SecurityHeroGraphic.tsx** — Landing page hero.

## Agent (GAN-like tester)

- **agent/api.py** — FastAPI: `POST /run-scan` (returns all at end), `POST /run-scan/stream` (SSE). Reads `.env` from agent dir.
- **agent/orchestrator.py** — Generator (Minimax) + Discriminator (Browser Use), optional `on_error_report` for streaming.
- **agent/config.py**, **agent/generator.py**, **agent/discriminator.py**, **agent/schemas.py** — Config, workflow generation, browser runs, data shapes.

## Fixer (optional, not in UI)

- **fixer/api.py** — FastAPI: rebuild/fix pipeline.
- **fixer/github_bot.py**, **fixer/patch_engine.py**, **fixer/repo_mapper.py**, **fixer/sandbox_verify.py** — GitHub PR, patches, routing, sandbox.

## How to run

1. Start agent: `cd agent && .venv/bin/python -m api` (port 8002).
2. Start Next: `npm run dev` (port 3000). Use `/dashboard` to analyze.
