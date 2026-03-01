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
