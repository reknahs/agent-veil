import { NextResponse } from "next/server";

export async function POST(req: Request) {
    try {
        const body = await req.json();
        const fixerUrl = process.env.FIXER_API_URL || "http://localhost:8001/fix-workflow";

        const response = await fetch(fixerUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: "Unknown error" }));
            return NextResponse.json({ ok: false, message: errorData.message || "Fixer API error" }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error: any) {
        console.error("Fixer proxy error:", error);
        return NextResponse.json({ ok: false, message: error.message }, { status: 500 });
    }
}
