import { NextResponse } from "next/server";

const AGENT_API_URL = process.env.AGENT_API_URL || process.env.NEXT_PUBLIC_AGENT_API_URL || "http://localhost:8002";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const base = AGENT_API_URL.replace(/\/$/, "");
    const res = await fetch(`${base}/run-scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({
      ok: false,
      summary: "",
      message: res.statusText || `Agent returned ${res.status}`,
    }));
    return NextResponse.json(data, { status: res.ok ? 200 : res.status });
  } catch (e) {
    const message =
      e instanceof Error ? e.message : "Request failed";
    return NextResponse.json(
      {
        ok: false,
        summary: "",
        message: `Agent unreachable: ${message}. Start the agent (e.g. cd agent && python -m api).`,
      },
      { status: 502 }
    );
  }
}
