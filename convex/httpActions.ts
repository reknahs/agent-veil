import { httpAction } from "./_generated/server.js";
import { internal } from "./_generated/api.js";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export const getBreaches = httpAction(async (ctx) => {
  const breaches = await ctx.runQuery(internal.queries.internalListBreaches);
  return new Response(JSON.stringify({ breaches }), {
    status: 200,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
});

export const postBreach = httpAction(async (ctx, request) => {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }
  if (request.method !== "POST") {
    return new Response("Method not allowed", { status: 405, headers: corsHeaders });
  }
  try {
    const body = await request.json();
    const url = body?.url;
    const type = body?.type;
    const screenshot_url = body?.screenshot_url;
    if (typeof url !== "string" || typeof type !== "string") {
      return new Response(JSON.stringify({ error: "url and type are required (strings)" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
    await ctx.runMutation(internal.mutations.internalAddBreach, {
      url,
      type,
      screenshot_url: typeof screenshot_url === "string" ? screenshot_url : undefined,
    });
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return new Response(JSON.stringify({ error: msg }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});

export const postLog = httpAction(async (ctx, request) => {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }
  if (request.method !== "POST") {
    return new Response("Method not allowed", { status: 405, headers: corsHeaders });
  }
  try {
    const body = await request.json();
    const message = body?.message;
    const level = body?.level;
    if (typeof message !== "string") {
      return new Response(JSON.stringify({ error: "message is required (string)" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
    const validLevels: ("info" | "success" | "warn" | "error")[] = ["info", "success", "warn", "error"];
    const l: "info" | "success" | "warn" | "error" =
      typeof level === "string" && validLevels.includes(level as "info" | "success" | "warn" | "error") ? (level as "info" | "success" | "warn" | "error") : "info";
    await ctx.runMutation(internal.mutations.internalInsertLog, { message, level: l });
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return new Response(JSON.stringify({ error: msg }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});

/** POST body: { targetUrl, githubRepo } → creates scan_run, returns { scanRunId } */
export const postScanStart = httpAction(async (ctx, request) => {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }
  if (request.method !== "POST") {
    return new Response("Method not allowed", { status: 405, headers: corsHeaders });
  }
  try {
    const body = (await request.json()) as Record<string, unknown>;
    const targetUrl = body?.targetUrl as string | undefined;
    const githubRepo = body?.githubRepo as string | undefined;
    if (!targetUrl || !githubRepo) {
      return new Response(JSON.stringify({ error: "targetUrl and githubRepo required" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
    const scanRunId = await ctx.runMutation(internal.mutations.internalInsertScanRun, {
      targetUrl,
      githubRepo,
      status: "running",
      startedAt: Date.now(),
    });
    return new Response(JSON.stringify({ scanRunId: scanRunId.toString() }), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return new Response(JSON.stringify({ error: msg }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});

/** POST body: { scanRunId, status, completedAt?, workflowCount? } */
export const postScanUpdate = httpAction(async (ctx, request) => {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }
  if (request.method !== "POST") {
    return new Response("Method not allowed", { status: 405, headers: corsHeaders });
  }
  try {
    const body = (await request.json()) as Record<string, unknown>;
    const scanRunId = body?.scanRunId as string | undefined;
    const status = body?.status as string | undefined;
    if (!scanRunId || !status || !["pending", "running", "completed", "failed"].includes(status)) {
      return new Response(JSON.stringify({ error: "scanRunId and status (pending|running|completed|failed) required" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
    await ctx.runMutation(internal.mutations.internalUpdateScanRun, {
      scanRunId: scanRunId as import("./_generated/dataModel").Id<"scan_runs">,
      status: status as "pending" | "running" | "completed" | "failed",
      completedAt: typeof body?.completedAt === "number" ? body.completedAt : undefined,
      workflowCount: typeof body?.workflowCount === "number" ? body.workflowCount : undefined,
    });
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return new Response(JSON.stringify({ error: msg }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});

/** POST body: { targetUrl?, title, issueSummary, description?, status?, taskId? } — ingest one agent-identified error for the UI cards */
export const postAgentError = httpAction(async (ctx, request) => {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }
  if (request.method !== "POST") {
    return new Response("Method not allowed", { status: 405, headers: corsHeaders });
  }
  try {
    const body = (await request.json()) as Record<string, unknown>;
    const title = body?.title as string | undefined;
    const issueSummary = body?.issueSummary as string | undefined;
    if (typeof title !== "string" || typeof issueSummary !== "string") {
      return new Response(
        JSON.stringify({ error: "title and issueSummary are required (strings)" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }
    await ctx.runMutation(internal.mutations.internalInsertAgentError, {
      targetUrl: typeof body?.targetUrl === "string" ? body.targetUrl : undefined,
      title,
      issueSummary,
      description: typeof body?.description === "string" ? body.description : undefined,
      status: typeof body?.status === "string" ? body.status : undefined,
      taskId: typeof body?.taskId === "string" ? body.taskId : undefined,
    });
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return new Response(JSON.stringify({ error: msg }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});

/** POST body: append { scanId, label } or update { workflowId, status, issue_summary?, steps?, step_count? } */
export const postWorkflow = httpAction(async (ctx, request) => {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }
  if (request.method !== "POST") {
    return new Response("Method not allowed", { status: 405, headers: corsHeaders });
  }
  try {
    const body = (await request.json()) as Record<string, unknown>;
    const workflowId = body?.workflowId as string | undefined;
    if (workflowId != null) {
      const status = body?.status as string | undefined;
      if (!status || !["pending", "ok", "has_issue"].includes(status)) {
        return new Response(JSON.stringify({ error: "workflowId requires status: pending|ok|has_issue" }), {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
      await ctx.runMutation(internal.mutations.internalUpdateWorkflowStatus, {
        workflowId: workflowId as import("./_generated/dataModel").Id<"workflows">,
        status: status as "pending" | "ok" | "has_issue",
        issue_summary: typeof body?.issue_summary === "string" ? body.issue_summary : undefined,
        steps: Array.isArray(body?.steps) ? (body.steps as string[]) : undefined,
        step_count: typeof body?.step_count === "number" ? body.step_count : undefined,
      });
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
    const scanId = body?.scanId as string | undefined;
    const label = body?.label as string | undefined;
    if (!scanId || typeof label !== "string") {
      return new Response(JSON.stringify({ error: "append requires scanId and label (strings)" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
    const id = await ctx.runMutation(internal.mutations.internalAppendWorkflow, {
      scanId,
      label,
      status: "pending",
    });
    return new Response(JSON.stringify({ ok: true, workflowId: id }), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return new Response(JSON.stringify({ error: msg }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
