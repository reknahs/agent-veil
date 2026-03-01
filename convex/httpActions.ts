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
