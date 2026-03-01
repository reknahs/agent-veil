# Setup Guide

## Run the APP with only the logic agent

1. **Agent API** (analyzes website + repo, returns findings):
   ```bash
   cd ../logic_agent
   python3 -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   cp .env.example .env        # then add BROWSER_USE_API_KEY, MINIMAX_API_KEY, MINIMAX_GROUP_ID
   python -m api
   ```
   Agent runs at `http://localhost:8002`.

2. **Next.js dashboard** (UI that calls the agent):
   ```bash
   npm install
   npm run dev
   ```
   Open `http://localhost:3000/dashboard`. Enter a website URL and optional GitHub repo, then click **Analyze**. Findings appear as cards (optionally streamed).

3. **Optional:** Set `AGENT_API_URL` or `NEXT_PUBLIC_AGENT_API_URL` (e.g. in `.env.local`) if the agent is not at `http://localhost:8002`.
