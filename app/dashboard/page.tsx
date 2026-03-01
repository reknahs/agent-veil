"use client";

import React, { useState, useEffect } from "react";

type ErrorItem = {
  title: string;
  issueSummary: string;
  description: string;
  status: string;
  pullRequestUrl?: string;
};

type ScanResult = {
  ok: boolean;
  summary: string;
  message: string;
  errors?: ErrorItem[];
};

type CardState = "Error" | "In progress" | "Completed";

function getCardKey(index: number, err: ErrorItem): string {
  const title = (err?.title ?? "").slice(0, 50);
  const summary = (err?.issueSummary ?? "").slice(0, 30);
  return `finding-${index}-${title}-${summary}`;
}

function getCardState(
  err: ErrorItem,
  cardKey: string,
  inProgressKeys: Set<string>,
  prUrlByKey: Record<string, string>
): CardState {
  const prUrl = err?.pullRequestUrl ?? prUrlByKey[cardKey];
  if (prUrl) return "Completed";
  if (inProgressKeys.has(cardKey)) return "In progress";
  return "Error";
}

function normalizeError(raw: unknown): ErrorItem {
  const o = raw && typeof raw === "object" ? raw as Record<string, unknown> : {};
  return {
    title: typeof o.title === "string" ? o.title : "Issue",
    issueSummary: typeof o.issueSummary === "string" ? o.issueSummary : String(o.error_summary ?? "—"),
    description: typeof o.description === "string" ? o.description : "",
    status: typeof o.status === "string" ? o.status : "issue",
    pullRequestUrl: typeof o.pullRequestUrl === "string" ? o.pullRequestUrl : undefined,
  };
}

export default function DashboardPage() {
  const [targetUrl, setTargetUrl] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [streamingErrors, setStreamingErrors] = useState<ErrorItem[]>([]);
  const [selectedError, setSelectedError] = useState<ErrorItem | null>(null);
  const [selectedErrorKey, setSelectedErrorKey] = useState<string | null>(null);
  const [inProgressKeys, setInProgressKeys] = useState<string[]>([]);
  const [prUrlByKey, setPrUrlByKey] = useState<Record<string, string>>({});
  const [fixPrLoading, setFixPrLoading] = useState(false);
  const [fixPrMessage, setFixPrMessage] = useState<string | null>(null);
  const inProgressSet = new Set(inProgressKeys);

  const handleCreatePullRequest = async (err: ErrorItem, cardKey: string) => {
    setFixPrMessage(null);
    setInProgressKeys((prev) => (prev.includes(cardKey) ? prev : [...prev, cardKey]));
    setFixPrLoading(true);
    try {
      const res = await fetch("/api/fix-workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          label: err.title,
          issue_summary: err.issueSummary,
          github_repo: githubRepo.trim() || undefined,
        }),
      });
      const data = (await res.json()) as { ok?: boolean; pr_url?: string; message?: string };
      if (data?.ok && data?.pr_url) {
        setPrUrlByKey((prev) => ({ ...prev, [cardKey]: data.pr_url! }));
        setInProgressKeys((prev) => prev.filter((k) => k !== cardKey));
        setFixPrMessage(data.message ?? "PR created");
      } else {
        setFixPrMessage(data?.message ?? "Fix PR failed");
        setInProgressKeys((prev) => prev.filter((k) => k !== cardKey));
      }
    } catch (e) {
      setFixPrMessage(e instanceof Error ? e.message : "Request failed");
      setInProgressKeys((prev) => prev.filter((k) => k !== cardKey));
    } finally {
      setFixPrLoading(false);
    }
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
    setInProgressKeys([]);
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
        const errs = Array.isArray(data.errors) ? data.errors.map(normalizeError) : [];
        setResult({
          ok: data.ok ?? false,
          summary: data.summary ?? "",
          message: data.message ?? "Request failed",
          errors: errs,
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
              setStreamingErrors((prev) => [...(prev || []), normalizeError(item.payload)]);
            } else if (item.type === "done") {
              const doneErrs = Array.isArray(item.errors) ? item.errors.map(normalizeError) : [];
              setResult({
                ok: item.ok ?? false,
                summary: item.summary ?? "",
                message: item.message ?? (doneErrs.length ? `Found ${doneErrs.length} issue(s).` : "No issues found."),
                errors: doneErrs,
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
        errors: [],
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
              <div className="finding-cards-grid" role="list">
                {(loading ? streamingErrors : result?.errors ?? []).map((err, i) => {
                  const cardKey = getCardKey(i, err);
                  const state = getCardState(err, cardKey, inProgressSet, prUrlByKey);
                  const safeTitle = err?.title ?? "Issue";
                  const safeSummary = err?.issueSummary ?? "";
                  return (
                    <button
                      key={cardKey}
                      type="button"
                      className="finding-card"
                      onClick={() => {
                        setSelectedError(err);
                        setSelectedErrorKey(cardKey);
                      }}
                      role="listitem"
                    >
                      <span className={`finding-card-state finding-card-state-${state.replace(/\s+/g, "-").toLowerCase()}`}>
                        {state}
                      </span>
                      <h3 className="finding-card-title">{safeTitle}</h3>
                      <p className="finding-card-description">{safeSummary || "Agent reported failure or bug."}</p>
                    </button>
                  );
                })}
              </div>
            )}

            {result && !result.ok && ((result?.errors?.length ?? 0) === 0 && !streamingErrors.length) && (
              <div className="finding-card finding-card-error" role="alert">
                <p>{result.message ?? "Something went wrong."}</p>
              </div>
            )}
          </section>
        )}
      </main>

      {selectedError && (
        <div
          className="finding-modal-backdrop"
          onClick={() => { setSelectedError(null); setFixPrMessage(null); }}
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
              onClick={() => { setSelectedError(null); setFixPrMessage(null); }}
              aria-label="Close"
            >
              ×
            </button>
            <div className="finding-modal-content">
              {(() => {
                const modalKey = selectedErrorKey ?? `modal-${(selectedError.title ?? "").slice(0, 40)}`;
                const modalState = getCardState(selectedError, modalKey, inProgressSet, prUrlByKey);
                const modalPrUrl = selectedError.pullRequestUrl ?? prUrlByKey[modalKey];
                return (
                  <>
                    <span className={`finding-modal-status finding-modal-status-${modalState.replace(/\s+/g, "-").toLowerCase()}`}>
                      {modalState}
                    </span>
                    {fixPrMessage && (
                      <div className="finding-modal-section">
                        <p className={modalPrUrl ? "finding-modal-summary" : "finding-modal-error"}>{fixPrMessage}</p>
                      </div>
                    )}
                  </>
                );
              })()}
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
              {(selectedError.pullRequestUrl ?? prUrlByKey[selectedErrorKey ?? ""]) && (
                <div className="finding-modal-section finding-modal-pr">
                  <h4 className="finding-modal-label">Pull request</h4>
                  <a
                    href={selectedError.pullRequestUrl ?? prUrlByKey[selectedErrorKey ?? ""]}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="finding-modal-pr-link"
                  >
                    View pull request →
                  </a>
                </div>
              )}
              <div className="finding-modal-actions">
                {(selectedError.pullRequestUrl ?? prUrlByKey[selectedErrorKey ?? ""]) ? (
                  <a
                    href={selectedError.pullRequestUrl ?? prUrlByKey[selectedErrorKey ?? ""]}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="finding-modal-btn finding-modal-btn-primary"
                  >
                    View pull request
                  </a>
                ) : (
                  <button
                    type="button"
                    className="finding-modal-btn finding-modal-btn-primary"
                    onClick={() => handleCreatePullRequest(selectedError, selectedErrorKey ?? `modal-${(selectedError.title ?? "").slice(0, 40)}`)}
                    disabled={fixPrLoading}
                  >
                    {fixPrLoading ? "Creating PR…" : "Fix PR request"}
                  </button>
                )}
                <button
                  type="button"
                  className="finding-modal-btn finding-modal-btn-secondary"
                  onClick={() => { setSelectedError(null); setFixPrMessage(null); }}
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
