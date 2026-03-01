# Deploying AgentVeil

To take AgentVeil to production, you must split the hosting into two platforms: **Vercel** for the Next.js frontend, and **Daytona** for the Python AI microservices. This is because Vercel's serverless functions have strict 10-second timeouts and cannot run headless Chromium browsers, while Daytona provides powerful, persistent AI workspaces.

---

### Step 1: Deploy the Database to Convex
1. Make sure your Convex schema is up to date.
2. Run `npx convex deploy` in your terminal to easily push your database rules and functions to Convex Cloud.

---

### Step 2: Deploy the Python Agents to Daytona
Since Daytona provides a persistent, full-featured development environment, we will use it as a robust cloud server to run your three AI agents.

1. Commit your code and push it to a GitHub repository.
2. Log into **Daytona** and link your GitHub account.
3. Click **Create Workspace** and select your AgentVeil repository.
4. Once the Daytona workspace spins up, open its terminal and set up your environment by running:
   ```bash
   pip install -r logic_agent/requirements.txt
   pip install -r fixer/requirements.txt
   playwright install --with-deps chromium
   ```
5. Create a `.env` file in the root of your Daytona workspace and add your keys:
   ```env
   MINIMAX_API_KEY=your_key_here
   MINIMAX_GROUP_ID=your_group_id
   BROWSER_USE_API_KEY=your_browser_use_key
   GITHUB_TOKEN=your_github_token
   ```
6. Start all three agents in the background so they keep running even if you close the Daytona window:
   ```bash
   nohup python logic_agent/api.py > logic.log 2>&1 &
   nohup python -m ui_agent.api > ui.log 2>&1 &
   nohup python -m fixer.api > fixer.log 2>&1 &
   ```
7. **Expose the Ports:** In Daytona, forward ports `8000` (Logic), `8001` (Fixer), and `8002` (UI), and make them public. Copy the **Public URL** for port 8001.

---

### Step 3: Deploy the Frontend to Vercel
Now that your Daytona workspace is running your Python AI backend 24/7, you can deploy the dashboard.

1. Go to [Vercel.com](https://vercel.com) and import your AgentVeil GitHub repository.
2. The framework preset should auto-detect as **Next.js**.
3. Under Environment Variables, add:
   - `NEXT_PUBLIC_CONVEX_URL`: Your production Convex URL.
   - `FIXER_API_URL`: The public Daytona URL you copied for port 8001 (e.g., `https://your-daytona-url-8001.daytona.app/fix-workflow/`).
4. Click **Deploy**.

**You're done!** Your Vercel dashboard will now trigger real-time, long-running AI agents hosted securely on Daytona using your $100 credits.
