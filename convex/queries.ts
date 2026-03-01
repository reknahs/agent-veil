import { query, internalQuery } from "./_generated/server.js";
import { v } from "convex/values";

export const internalListBreaches = internalQuery({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("breaches").collect();
  },
});

export const listBreaches = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("breaches").collect();
  },
});

export const listLogs = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, { limit = 100 }) => {
    const logs = await ctx.db
      .query("logs")
      .withIndex("by_timestamp")
      .order("desc")
      .take(limit);
    return logs.reverse();
  },
});

export const getPrStatus = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("pr_status").first();
  },
});

export const listWorkflows = query({
  args: { scanId: v.optional(v.string()) },
  handler: async (ctx, { scanId }) => {
    const effectiveScanId = scanId ?? (await ctx.db.query("scan_runs").withIndex("by_startedAt").order("desc").first())?._id?.toString();
    if (effectiveScanId) {
      return await ctx.db
        .query("workflows")
        .withIndex("by_scan", (q) => q.eq("scanId", effectiveScanId))
        .collect();
    }
    return [];
  },
});

export const getScanStatus = query({
  args: {},
  handler: async (ctx) => {
    const run = await ctx.db
      .query("scan_runs")
      .withIndex("by_startedAt")
      .order("desc")
      .first();
    return run ?? null;
  },
});

export const internalListWorkflows = internalQuery({
  args: { scanId: v.optional(v.string()) },
  handler: async (ctx, { scanId }) => {
    if (scanId) {
      return await ctx.db
        .query("workflows")
        .withIndex("by_scan", (q) => q.eq("scanId", scanId))
        .collect();
    }
    return await ctx.db
      .query("workflows")
      .withIndex("by_runAt")
      .order("desc")
      .take(100);
  },
});
