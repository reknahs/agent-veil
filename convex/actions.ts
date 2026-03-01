import { v } from "convex/values";
import { action } from "./_generated/server.js";
import { internal } from "./_generated/api";

/**
 * Launch Attack — demo mode only.
 * When you click "Launch Attack" with demo: true, this action:
 * 1. Inserts sample "agent thought" logs (e.g. "Attempting IDOR on /api/user... Success.")
 * 2. Inserts two breach records: /api/user (IDOR) and /api/orders (Auth Bypass)
 *
 * The dashboard then shows: red nodes for those URLs, and the logs in the feed.
 * In production, this would trigger a real security scan pipeline instead.
 */
export const launchAttack = action({
  args: { demo: v.optional(v.boolean()) },
  handler: async (ctx, { demo }) => {
    if (demo) {
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
 * Rebuild Security — sets PR status to pending then "created" with a placeholder PR URL.
 * In production this would call your API or GitHub to open a real fix PR.
 */
export const rebuildSecurity = action({
  args: {},
  handler: async (ctx) => {
    await ctx.runMutation(internal.mutations.internalSetPrStatus, {
      status: "pending",
      message: "Creating fix PR...",
    });
    await new Promise((r) => setTimeout(r, 1500));
    const prUrl = "https://github.com/your-org/your-repo/pull/1";
    await ctx.runMutation(internal.mutations.internalSetPrStatus, {
      status: "created",
      pr_url: prUrl,
      message: "Fix PR created.",
    });
    return { ok: true, pr_url: prUrl };
  },
});
