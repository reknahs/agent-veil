# What “Launch Attack” does

**Launch Attack** is a **demo-only** button. It does not run a real security scan.

When you click it, the frontend calls the Convex action `actions:launchAttack` with `{ demo: true }`. That action:

1. **Writes sample logs** to the `logs` table, e.g.:
   - "Attempting IDOR on /api/user..."
   - "Attempting IDOR on /api/user... Success."
   - "Checking /api/orders for auth bypass..."
   - "Auth bypass on /api/orders confirmed."

2. **Writes two breach records** to the `breaches` table:
   - `/api/user` — type `IDOR`
   - `/api/orders` — type `Auth Bypass`

The dashboard then:

- **Attack graph:** nodes for `/api/user` and `/api/orders` turn **red** (only for breaches that happened after the page loaded).
- **Breach feed:** the new log lines show up in “Agent thoughts.”

In a real setup, “Launch Attack” would start a real scanner (e.g. Person 1’s pipeline), which would run tests and then write real breaches/logs to Convex.

---

## How to test it

1. **Deploy the Convex backend** (one terminal):
   ```bash
   npx convex dev
   ```
   Log in at convex.dev if needed and create/link a project. Wait until you see Convex functions ready.

2. **Set the Convex URL** in `.env.local`:
   ```bash
   NEXT_PUBLIC_CONVEX_URL=https://YOUR-DEPLOYMENT.convex.cloud
   ```
   Get the URL from the Convex dashboard → your project → Settings → URL.

3. **Run the Next.js app** (second terminal):
   ```bash
   npm run dev:next
   ```

4. **Open** http://localhost:3000  
   - Graph should start with **no red nodes** (only breaches after page load count).
   - Click **Launch Attack** → two nodes turn red and the feed shows the sample logs.
