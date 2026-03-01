import { v } from "convex/values";
import { action } from "./_generated/server.js";
import { internal } from "./_generated/api";

const FIXER_API_URL = process.env.FIXER_API_URL ?? "";
const ORCHESTRATOR_API_URL = process.env.ORCHESTRATOR_API_URL ?? "";

/**
 * Launch Attack — inserts sample logs/breaches for the given target URL (demo).
 */
export const launchAttack = action({
  args: { demo: v.optional(v.boolean()), target_url: v.optional(v.string()) },
  handler: async (ctx, { demo = true, target_url }) => {
    const base = target_url ?? "http://localhost:3000";
    const isStaticSite = base.includes("jayadevgh.github.io") || base.includes("github.io");
    if (isStaticSite) {
      await ctx.runMutation(internal.mutations.internalInsertLog, {
        message: "Running Shields Up (security headers) on static site...",
        level: "info",
      });
      await ctx.runMutation(internal.mutations.internalInsertLog, {
        message: "Missing headers: Content-Security-Policy, X-Frame-Options",
        level: "success",
      });
      await ctx.runMutation(internal.mutations.internalAddBreach, {
        url: "/",
        type: "Missing Headers",
      });
      await ctx.runMutation(internal.mutations.internalInsertLog, {
        message: "Checking /about...",
        level: "info",
      });
      await ctx.runMutation(internal.mutations.internalAddBreach, {
        url: "/about",
        type: "Missing Headers",
      });
    } else {
      await ctx.runMutation(internal.mutations.internalInsertLog, {
        message: "Attempting IDOR on /api/user...",
        level: "info",
      });
      await ctx.runMutation(internal.mutations.internalInsertLog, {
        message: "Attempting IDOR on /api/user... Success.",
        level: "success",
      });
      await ctx.runMutation(internal.mutations.internalAddBreach, {
        url: "/api/user",
        type: "IDOR",
      });
      await ctx.runMutation(internal.mutations.internalInsertLog, {
        message: "Checking /api/orders for auth bypass...",
        level: "info",
      });
      await ctx.runMutation(internal.mutations.internalInsertLog, {
        message: "Auth bypass on /api/orders confirmed.",
        level: "success",
      });
      await ctx.runMutation(internal.mutations.internalAddBreach, {
        url: "/api/orders",
        type: "Auth Bypass",
      });
    }
    return { ok: true };
  },
});

/**
 * Rebuild Security — calls the Fixer API to create a PR from breaches.
 * If FIXER_API_URL is set, fetches breaches and POSTs to fixer. Otherwise uses demo placeholder.
 */
export const rebuildSecurity = action({
  args: {
    github_repo: v.optional(v.string()),
    single_breach: v.optional(v.object({ url: v.string(), type: v.string() })),
  },
  handler: async (ctx, { github_repo, single_breach }) => {
    await ctx.runMutation(internal.mutations.internalSetPrStatus, {
      status: "pending",
      message: "Creating fix PR...",
    });

    if (FIXER_API_URL) {
      try {
        const breaches = single_breach
          ? [{ url: single_breach.url, type: single_breach.type }]
          : (await ctx.runQuery(internal.queries.internalListBreaches)).map((b) => ({
              url: b.url,
              type: b.type,
              screenshot_url: b.screenshot_url ?? undefined,
            }));
        const body: Record<string, unknown> = { breaches };
        if (github_repo) body.repo_full_name = github_repo;
        const res = await fetch(`${FIXER_API_URL}/rebuild`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const data = (await res.json()) as { ok?: boolean; pr_url?: string; message?: string };
        const prUrl = data?.pr_url;
        const msg = data?.message ?? (res.ok ? "Fix PR created" : "Fixer API error");
        await ctx.runMutation(internal.mutations.internalSetPrStatus, {
          status: prUrl ? "created" : "failed",
          pr_url: prUrl,
          message: msg,
        });
        return { ok: !!data?.ok, pr_url: prUrl ?? undefined };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        await ctx.runMutation(internal.mutations.internalSetPrStatus, {
          status: "failed",
          message: `Fixer error: ${msg}`,
        });
        return { ok: false };
      }
    }

    // Demo fallback — use github_repo if provided, otherwise placeholder
    await new Promise((r) => setTimeout(r, 500));
    const repoSlug = github_repo
      ? github_repo.replace(/^https?:\/\/github\.com\/?/, "").replace(/\/$/, "") || undefined
      : undefined;
    const prUrl = repoSlug
      ? `https://github.com/${repoSlug}/pull/1`
      : null;
    const message = prUrl
      ? `Demo: PR would target ${repoSlug}. To create real PRs: run the fixer (GITHUB_TOKEN, GEMINI_API_KEY), set FIXER_API_URL in Convex, and enter the repo above.`
      : "Demo mode. Enter GitHub Repo (e.g. owner/repo) and set FIXER_API_URL to create real PRs.";
    await ctx.runMutation(internal.mutations.internalSetPrStatus, {
      status: "created",
      pr_url: prUrl ?? undefined,
      message,
    });
    return { ok: true, pr_url: prUrl ?? undefined };
  },
});

/**
 * Start workflow scan: clear old workflows, then trigger orchestrator (url + repo).
 * Orchestrator creates scan run in Convex and runs LLM + Browser Use in background.
 */
export const startWorkflowScan = action({
  args: {
    target_url: v.string(),
    github_repo: v.string(),
  },
  handler: async (ctx, { target_url, github_repo }) => {
    await ctx.runMutation(internal.mutations.internalClearWorkflows);

    if (!ORCHESTRATOR_API_URL) {
      await ctx.runMutation(internal.mutations.internalInsertLog, {
        message: "Workflow scan skipped: set ORCHESTRATOR_API_URL and run scanner (see scanner/api.py)",
        level: "warn",
      });
      return { ok: false, error: "ORCHESTRATOR_API_URL not set" };
    }

    try {
      const res = await fetch(`${ORCHESTRATOR_API_URL}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_url: target_url.trim(),
          github_repo: github_repo.trim().replace(/^https?:\/\/github\.com\/?/, "").replace(/\/$/, ""),
        }),
      });
      const data = (await res.json()) as { ok?: boolean; scanRunId?: string; error?: string };
      if (data?.ok && data.scanRunId) {
        await ctx.runMutation(internal.mutations.internalInsertLog, {
          message: `Workflow scan started (scanRunId: ${data.scanRunId}). Watch the graph for progress.`,
          level: "info",
        });
        return { ok: true, scanRunId: data.scanRunId };
      }
      return { ok: false, error: data?.error ?? "Orchestrator did not return scanRunId" };
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      await ctx.runMutation(internal.mutations.internalInsertLog, {
        message: `Workflow scan failed: ${msg}`,
        level: "error",
      });
      return { ok: false, error: msg };
    }
  },
});
