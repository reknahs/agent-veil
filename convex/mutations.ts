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
    return { ok: true };
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
