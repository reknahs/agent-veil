"use client";

import React, { useState, useEffect } from "react";

type ErrorItem = { title: string; issueSummary: string; description: string; status: string };

type ScanResult = {
  ok: boolean;
  summary: string;
  message: string;
  errors?: ErrorItem[];
};

type CardState = "Completed" | "In process" | "Unseen";

function getCardState(err: ErrorItem): CardState {
  const s = (err.status || "").toLowerCase();
  if (s === "finished") return "Completed";
  if (s === "stopped" || s === "error") return "In process";
  return "Unseen";
}

export default function DashboardPage() {
  const [targetUrl, setTargetUrl] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [streamingErrors, setStreamingErrors] = useState<ErrorItem[]>([]);
  const [selectedError, setSelectedError] = useState<ErrorItem | null>(null);

  const handleCreatePullRequest = (err: ErrorItem) => {
    // Placeholder: will connect to build module later
    setSelectedError(null);
    // TODO: call build module with err (e.g. title + issueSummary for PR body)
  };

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSelectedError(null);
    };
    if (selectedError) {
      document.addEventListener("keydown", onKeyDown);
      return () => document.removeEventListener("keydown", onKeyDown);
    }
  }, [selectedError]);

  const handleAnalyze = async () => {
    if (!targetUrl.trim()) return;
    setLoading(true);
    setResult(null);
    setStreamingErrors([]);
    const payload = {
      target_url: targetUrl.trim(),
      github_repo: githubRepo.trim() || undefined,
      site_description: undefined,
    };
    try {
      const res = await fetch("/api/run-scan/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const contentType = res.headers.get("content-type") || "";
      const isJson = contentType.includes("application/json");

      if (!res.ok || isJson) {
        const data: ScanResult = await res.json().catch(() => ({
          ok: false,
          summary: "",
          message: res.statusText || `HTTP ${res.status}`,
          errors: [],
        }));
        setResult({
          ok: data.ok ?? false,
          summary: "",
          message: data.message ?? "",
          errors: data.errors ?? [],
        });
        setLoading(false);
        return;
      }
      if (!res.body) {
        setLoading(false);
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() ?? "";
        for (const chunk of lines) {
          const match = chunk.match(/^data:\s*(.+)/m);
          if (!match) continue;
          try {
            const item = JSON.parse(match[1].trim());
            if (item.type === "error" && item.payload) {
              setStreamingErrors((prev) => [...(prev || []), item.payload]);
            } else if (item.type === "done") {
              setResult({
                ok: item.ok ?? false,
                summary: "",
                message: item.message ?? "",
                errors: item.errors ?? [],
              });
            } else if (item.type === "error" && item.message) {
              setResult({
                ok: false,
                summary: "",
                message: item.message,
                errors: [],
              });
            }
          } catch {
            // ignore parse errors for partial chunks
          }
        }
      }
    } catch (e) {
      const msg =
        e instanceof TypeError && e.message === "Failed to fetch"
          ? "Could not reach the agent API. Start it from the agent folder: python -m api (or uvicorn api:app --port 8002)"
          : e instanceof Error
            ? e.message
            : "Request failed";
      setResult({
        ok: false,
        summary: "",
        message: msg,
      });
    } finally {
      setLoading(false);
      setStreamingErrors([]);
    }
  };

  const canAnalyze = targetUrl.trim().length > 0;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="dashboard-header-top">
          <div className="dashboard-title-block">
            <h1>Security Cartographer</h1>
            <p className="dashboard-tagline">Analyze a website and GitHub repo</p>
          </div>
        </div>

        <div className="dashboard-target-row">
          <label htmlFor="target-url" className="target-label">
            Website URL
          </label>
          <input
            id="target-url"
            type="url"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            placeholder="https://example.com"
            className="target-input"
          />
          <label htmlFor="github-repo" className="target-label">
            GitHub Repo
          </label>
          <input
            id="github-repo"
            type="text"
            value={githubRepo}
            onChange={(e) => setGithubRepo(e.target.value)}
            placeholder="owner/repo (optional)"
            className="target-input"
          />
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={loading || !canAnalyze}
            title={!canAnalyze ? "Enter Website URL first" : undefined}
          >
            {loading ? "Analyzing…" : "Analyze"}
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        {(result || loading) && (
          <section className="findings-section">
            <header className="findings-header">
              <h2 className="findings-title">Findings</h2>
              {loading && streamingErrors.length === 0 && !result && (
                <span className="findings-badge findings-badge-loading">Analyzing…</span>
              )}
              {result?.message && !loading && (
                <span className="findings-count">{result.message}</span>
              )}
              {loading && streamingErrors.length > 0 && (
                <span className="findings-count">{streamingErrors.length} issue(s) so far…</span>
              )}
            </header>

            {!result?.errors?.length && !streamingErrors.length && result?.ok && !loading && (
              <div className="finding-card finding-card-empty">
                <p>No issues found.</p>
              </div>
            )}

            {((result?.errors?.length ?? 0) > 0 || streamingErrors.length > 0) && (
              <div className="finding-cards-grid">
                {(loading ? streamingErrors : result?.errors ?? []).map((err, i) => {
                  const state = getCardState(err);
                  return (
                    <button
                      key={i}
                      type="button"
                      className="finding-card"
                      onClick={() => setSelectedError(err)}
                    >
                      <span className={`finding-card-state finding-card-state-${state.replace(/\s+/g, "-").toLowerCase()}`}>
                        {state}
                      </span>
                      <h3 className="finding-card-title">{err.title}</h3>
                      <p className="finding-card-description">{err.issueSummary}</p>
                    </button>
                  );
                })}
              </div>
            )}

            {result && !result.ok && ((result?.errors?.length ?? 0) === 0 && !streamingErrors.length) && (
              <div className="finding-card finding-card-error">
                <p>{result.message}</p>
              </div>
            )}
          </section>
        )}
      </main>

      {selectedError && (
        <div
          className="finding-modal-backdrop"
          onClick={() => setSelectedError(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="finding-modal-title"
        >
          <div
            className="finding-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="finding-modal-close"
              onClick={() => setSelectedError(null)}
              aria-label="Close"
            >
              ×
            </button>
            <div className="finding-modal-content">
              <span className={`finding-modal-status finding-modal-status-${(selectedError.status || "issue").toLowerCase()}`}>
                {selectedError.status || "Issue"}
              </span>
              <h2 id="finding-modal-title" className="finding-modal-title">
                {selectedError.title}
              </h2>
              <div className="finding-modal-section">
                <h4 className="finding-modal-label">Summary</h4>
                <p className="finding-modal-summary">{selectedError.issueSummary}</p>
              </div>
              {selectedError.description && (
                <div className="finding-modal-section">
                  <h4 className="finding-modal-label">Description</h4>
                  <pre className="finding-modal-description">{selectedError.description}</pre>
                </div>
              )}
              <div className="finding-modal-actions">
                <button
                  type="button"
                  className="finding-modal-btn finding-modal-btn-primary"
                  onClick={() => handleCreatePullRequest(selectedError)}
                >
                  Create pull request
                </button>
                <button
                  type="button"
                  className="finding-modal-btn finding-modal-btn-secondary"
                  onClick={() => setSelectedError(null)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
