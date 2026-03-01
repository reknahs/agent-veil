import { mutation, internalMutation } from "./_generated/server.js";
import { v } from "convex/values";

export const insertLog = mutation({
  args: {
    message: v.string(),
    level: v.optional(
      v.union(
        v.literal("info"),
        v.literal("success"),
        v.literal("warn"),
        v.literal("error")
      )
    ),
  },
  handler: async (
    ctx,
    args: { message: string; level?: "info" | "success" | "warn" | "error" }
  ) => {
    const { message, level } = args;
    return await ctx.db.insert("logs", {
      timestamp: Date.now(),
      message,
      level: level ?? "info",
    });
  },
});

export const addBreach = mutation({
  args: {
    url: v.string(),
    type: v.string(),
    screenshot_url: v.optional(v.string()),
  },
  handler: async (
    ctx,
    args: { url: string; type: string; screenshot_url?: string }
  ) => {
    const { url, type, screenshot_url } = args;
    return await ctx.db.insert("breaches", {
      url,
      type,
      screenshot_url,
      confirmedAt: Date.now(),
    });
  },
});

export const setPrStatus = mutation({
  args: {
    status: v.union(
      v.literal("idle"),
      v.literal("pending"),
      v.literal("created"),
      v.literal("failed")
    ),
    pr_url: v.optional(v.string()),
    message: v.optional(v.string()),
  },
  handler: async (
    ctx,
    args: { status: "idle" | "pending" | "created" | "failed"; pr_url?: string; message?: string }
  ) => {
    const { status, pr_url, message } = args;
    const existing = await ctx.db.query("pr_status").first();
    const now = Date.now();
    if (existing) {
      await ctx.db.patch(existing._id, { status, pr_url, message, updatedAt: now });
      return existing._id;
    }
    return await ctx.db.insert("pr_status", {
      status,
      pr_url,
      message,
      updatedAt: now,
    });
  },
});

export const internalInsertLog = internalMutation({
  args: {
    message: v.string(),
    level: v.optional(
      v.union(
        v.literal("info"),
        v.literal("success"),
        v.literal("warn"),
        v.literal("error")
      )
    ),
  },
  handler: async (
    ctx,
    args: { message: string; level?: "info" | "success" | "warn" | "error" }
  ) => {
    const { message, level } = args;
    return await ctx.db.insert("logs", {
      timestamp: Date.now(),
      message,
      level: level ?? "info",
    });
  },
});

export const internalAddBreach = internalMutation({
  args: {
    url: v.string(),
    type: v.string(),
    screenshot_url: v.optional(v.string()),
  },
  handler: async (
    ctx,
    args: { url: string; type: string; screenshot_url?: string }
  ) => {
    const { url, type, screenshot_url } = args;
    return await ctx.db.insert("breaches", {
      url,
      type,
      screenshot_url,
      confirmedAt: Date.now(),
    });
  },
});

export const clearDemoData = mutation({
  args: {},
  handler: async (ctx) => {
    const breaches = await ctx.db.query("breaches").collect();
    for (const b of breaches) {
      await ctx.db.delete(b._id);
    }
    const logs = await ctx.db.query("logs").collect();
    for (const l of logs) {
      await ctx.db.delete(l._id);
    }
    const pr = await ctx.db.query("pr_status").first();
    if (pr) {
      await ctx.db.patch(pr._id, {
        status: "idle",
        pr_url: undefined,
        message: undefined,
        updatedAt: Date.now(),
      });
    }
    const workflows = await ctx.db.query("workflows").collect();
    for (const w of workflows) await ctx.db.delete(w._id);
    const scanRuns = await ctx.db.query("scan_runs").collect();
    for (const r of scanRuns) await ctx.db.delete(r._id);
    return { ok: true };
  },
});

export const internalAppendWorkflow = internalMutation({
  args: {
    scanId: v.string(),
    label: v.string(),
    status: v.union(
      v.literal("pending"),
      v.literal("ok"),
      v.literal("has_issue")
    ),
    issue_summary: v.optional(v.string()),
    steps: v.optional(v.array(v.string())),
    step_count: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const runAt = Date.now();
    return await ctx.db.insert("workflows", {
      ...args,
      runAt,
    });
  },
});

export const internalUpdateWorkflowStatus = internalMutation({
  args: {
    workflowId: v.id("workflows"),
    status: v.union(
      v.literal("pending"),
      v.literal("ok"),
      v.literal("has_issue")
    ),
    issue_summary: v.optional(v.string()),
    steps: v.optional(v.array(v.string())),
    step_count: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const { workflowId, ...patch } = args;
    await ctx.db.patch(workflowId, patch);
    return workflowId;
  },
});

export const internalClearWorkflows = internalMutation({
  args: {},
  handler: async (ctx) => {
    const all = await ctx.db.query("workflows").collect();
    for (const w of all) await ctx.db.delete(w._id);
    return { deleted: all.length };
  },
});

export const internalClearScanRuns = internalMutation({
  args: {},
  handler: async (ctx) => {
    const all = await ctx.db.query("scan_runs").collect();
    for (const r of all) await ctx.db.delete(r._id);
    return { deleted: all.length };
  },
});

export const internalInsertScanRun = internalMutation({
  args: {
    targetUrl: v.string(),
    githubRepo: v.string(),
    status: v.union(
      v.literal("pending"),
      v.literal("running"),
      v.literal("completed"),
      v.literal("failed")
    ),
    startedAt: v.number(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("scan_runs", args);
  },
});

export const internalUpdateScanRun = internalMutation({
  args: {
    scanRunId: v.id("scan_runs"),
    status: v.union(
      v.literal("pending"),
      v.literal("running"),
      v.literal("completed"),
      v.literal("failed")
    ),
    completedAt: v.optional(v.number()),
    workflowCount: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const { scanRunId, ...patch } = args;
    await ctx.db.patch(scanRunId, patch);
    return scanRunId;
  },
});

export const internalSetPrStatus = internalMutation({
  args: {
    status: v.union(
      v.literal("idle"),
      v.literal("pending"),
      v.literal("created"),
      v.literal("failed")
    ),
    pr_url: v.optional(v.string()),
    message: v.optional(v.string()),
  },
  handler: async (
    ctx,
    args: { status: "idle" | "pending" | "created" | "failed"; pr_url?: string; message?: string }
  ) => {
    const { status, pr_url, message } = args;
    const existing = await ctx.db.query("pr_status").first();
    const now = Date.now();
    if (existing) {
      await ctx.db.patch(existing._id, { status, pr_url, message, updatedAt: now });
      return existing._id;
    }
    return await ctx.db.insert("pr_status", {
      status,
      pr_url,
      message,
      updatedAt: now,
    });
  },
});
