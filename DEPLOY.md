# Deploying AgentVeil For Free

To host this project completely for free, we will use **Vercel** (Free Tier) for the Next.js frontend, **Convex** (Free Tier) for the database, and your **$100 Daytona Credits** for the Python AI microservices. 

*(Note: We cannot use Render.com's free tier because the AI agents use headless Chromium browsers, which exceed Render's free RAM limits. Daytona's cloud workspaces are powerful enough to run this.)*

---

### Step 1: Deploy the Database to Convex (Free)
1. Make sure your Convex schema is up to date.
2. Run `npx convex deploy` in your terminal to easily push your database rules and functions to Convex Cloud.

---

### Step 2: Deploy the Python Agents to Daytona (Using $100 Credits)
Daytona provides a persistent, full-featured development workspace. This will act as our robust cloud server.

1. Go to **[Daytona](https://daytona.io/)** and log in with your GitHub account to access your sponsor credits.
2. Click **Create Workspace** and select your AgentVeil GitHub repository.
3. Once the Daytona workspace loads, open its terminal and install the exact dependencies by copy-pasting this block:
   ```bash
   pip install -r logic_agent/requirements.txt
   pip install -r fixer/requirements.txt
   playwright install --with-deps chromium
   ```
4. Create a `.env` file in the root of your Daytona workspace and add your keys:
   ```env
   MINIMAX_API_KEY=your_key_here
   MINIMAX_GROUP_ID=your_group_id
   BROWSER_USE_API_KEY=your_browser_use_key
   GITHUB_TOKEN=your_github_token
   ```
5. Start all three agents in the background. Using `nohup` ensures they stay online 24/7 forever, even when you close the Daytona tab:
   ```bash
   nohup python logic_agent/api.py > logic.log 2>&1 &
   nohup python -m ui_agent.api > ui.log 2>&1 &
   nohup python -m fixer.api > fixer.log 2>&1 &
   ```
6. **Expose the Ports:** Look at the bottom dock in Daytona and click on the **Ports** tab. 
   - Click **Forward Port** and map port `8001`.
   - Ensure the visibility is set to **Public**.
   - Copy the **Forwarded URL** for port 8001.

---

### Step 3: Deploy the Frontend to Vercel (Free)
Now that your Daytona workspace is running your Python AI backend 24/7, you can deploy the dashboard.

1. Go to **[Vercel.com](https://vercel.com)** and import your AgentVeil GitHub repository.
2. The framework preset should auto-detect as **Next.js**.
3. Under Environment Variables, add:
   - `NEXT_PUBLIC_CONVEX_URL`: Your production Convex URL.
   - `FIXER_API_URL`: The public Daytona URL you copied for port 8001 (e.g., `https://8001-your-daytona-url.daytonaproxy01.net/fix-workflow/`).
   - `AGENT_API_URL`: The Daytona URL pointing to the logic agent on port 8002 (e.g., `https://8002-your-daytona-url.daytonaproxy01.net`).
   - `UI_AGENT_API_URL`: The Daytona URL pointing to the UI agent on port 8000 (e.g., `https://8000-your-daytona-url.daytonaproxy01.net`).
4. Click **Deploy**.

**You're done!** Vercel runs your UI for free, Convex runs your DB for free, and Daytona runs your AI backend using your sponsor credits!
