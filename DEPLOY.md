# Deploying AgentVeil

To take AgentVeil to production, you must split the hosting into two platforms: **Vercel** for the Next.js frontend, and **Render** for the Python AI microservices. This is because Vercel's serverless functions have strict 10-second timeouts and cannot run headless Chromium browsers.

---

### Step 1: Deploy the Database to Convex
1. Make sure your Convex schema is up to date.
2. Run `npx convex deploy` in your terminal to easily push your database rules and functions to Convex Cloud.

---

### Step 2: Deploy the Python Agents to Render.com
We have pre-configured a `Dockerfile` and a `render.yaml` Infrastructure-as-Code Blueprint for you. This will automatically spin up the Logic, UI, and Fixer agents as three separate Dockerized Web Services.

1. Commit your code and push it to a GitHub repository.
2. Create an account at [Render.com](https://render.com) and link your GitHub.
3. In the Render Dashboard, go to **Blueprints** -> **New Blueprint Instance**.
4. Select your AgentVeil repository. Render will automatically detect the `render.yaml` file.
5. Provide your API keys when prompted (`MINIMAX_API_KEY`, `BROWSER_USE_API_KEY`, `GITHUB_TOKEN`).
6. Click **Apply**. 

Render will build the Docker container (which installs Python, Playwright, and Chromium) and seamlessly deploy all three APIs!

---

### Step 3: Deploy the Frontend to Vercel
Now that your backend is running continuously on Render, you can deploy your dashboard.

1. Go to [Vercel.com](https://vercel.com) and import your AgentVeil GitHub repository.
2. The framework preset should auto-detect as **Next.js**.
3. Under Environment Variables, add:
   - `NEXT_PUBLIC_CONVEX_URL`: Your production Convex URL.
   - `FIXER_API_URL`: The URL of your newly spun-up Render Fixer service (e.g., `https://agentveil-fixer.onrender.com/fix-workflow`).
4. Click **Deploy**.

**You're done!** Your Vercel dashboard will now trigger real-time, long-running AI agents on Render.
