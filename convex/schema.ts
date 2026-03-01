import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  breaches: defineTable({
    url: v.string(),
    type: v.string(),
    screenshot_url: v.optional(v.string()),
    confirmedAt: v.number(),
  }).index("by_url", ["url"]),

  logs: defineTable({
    timestamp: v.number(),
    message: v.string(),
    level: v.optional(
      v.union(
        v.literal("info"),
        v.literal("success"),
        v.literal("warn"),
        v.literal("error")
      )
    ),
  }).index("by_timestamp", ["timestamp"]),

  pr_status: defineTable({
    status: v.union(
      v.literal("idle"),
      v.literal("pending"),
      v.literal("created"),
      v.literal("failed")
    ),
    pr_url: v.optional(v.string()),
    message: v.optional(v.string()),
    updatedAt: v.number(),
  }),
});
