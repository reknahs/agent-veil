import { NextRequest } from "next/server";

const FIXER_API_URL = process.env.FIXER_API_URL ?? "";

export async function POST(request: NextRequest) {
  if (!FIXER_API_URL) {
    return Response.json(
      {
        ok: false,
        message:
          "Fixer not configured. Set FIXER_API_URL (e.g. http://localhost:8001) and run the fixer: python -m fixer.api",
      },
      { status: 503 }
    );
  }

  try {
    const body = await request.json();
    const label = typeof body?.label === "string" ? body.label : "";
    const issue_summary = typeof body?.issue_summary === "string" ? body.issue_summary : "";
    const github_repo = typeof body?.github_repo === "string" ? body.github_repo.trim() : "";

    if (!label || !issue_summary) {
      return Response.json(
        { ok: false, message: "label and issue_summary are required" },
        { status: 400 }
      );
    }

    const repo_full_name = github_repo
      ? github_repo.replace(/^https?:\/\/github\.com\/?/, "").replace(/\/$/, "")
      : undefined;

    const base = FIXER_API_URL.replace(/\/$/, "");
    const res = await fetch(`${base}/fix-workflow`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        label,
        issue_summary,
        repo_full_name: repo_full_name || undefined,
        base_branch: "main",
      }),
    });

    const data = (await res.json()) as { ok?: boolean; pr_url?: string; message?: string };
    if (!res.ok) {
      return Response.json(
        { ok: false, message: data?.message ?? res.statusText },
        { status: res.status }
      );
    }
    return Response.json({
      ok: !!data?.ok,
      pr_url: data?.pr_url,
      message: data?.message ?? "Fix PR created",
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return Response.json({ ok: false, message: msg }, { status: 500 });
  }
}
