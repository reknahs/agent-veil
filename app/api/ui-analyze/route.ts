import { NextRequest } from "next/server";

const UI_AGENT_API_URL = process.env.UI_AGENT_API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
    const base = UI_AGENT_API_URL.replace(/\/$/, "");
    const body = await request.json();

    // UI Agent expects { url: string, max_steps?: number }
    const res = await fetch(`${base}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            url: body.target_url,
            max_steps: 55,
        }),
    });

    if (!res.ok || !res.body) {
        const text = await res.text();
        return new Response(JSON.stringify({ status: "error", message: text || res.statusText }), {
            status: res.status,
            headers: { "Content-Type": "application/json" },
        });
    }

    return new Response(res.body, {
        status: 200,
        headers: {
            "Content-Type": "application/x-ndjson",
            "Cache-Control": "no-cache",
            Connection: "keep-alive",
        },
    });
}
