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

  workflows: defineTable({
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
    runAt: v.number(),
  }).index("by_scan", ["scanId"]).index("by_runAt", ["runAt"]),

  scan_runs: defineTable({
    targetUrl: v.string(),
    githubRepo: v.string(),
    status: v.union(
      v.literal("pending"),
      v.literal("running"),
      v.literal("completed"),
      v.literal("failed")
    ),
    startedAt: v.number(),
    completedAt: v.optional(v.number()),
    workflowCount: v.optional(v.number()),
  }).index("by_startedAt", ["startedAt"]),

  agent_errors: defineTable({
    targetUrl: v.optional(v.string()),
    title: v.string(),
    issueSummary: v.string(),
    description: v.optional(v.string()),
    status: v.optional(v.string()),
    taskId: v.optional(v.string()),
    createdAt: v.number(),
  }).index("by_createdAt", ["createdAt"]),
});
