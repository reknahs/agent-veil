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

type UIResultItem = {
  status: "info" | "bug" | "done" | "error";
  message?: string;
  content?: string;
};


function getCardKey(index: number, err: ErrorItem): string {
  const title = (err?.title ?? "").slice(0, 50);
  const summary = (err?.issueSummary ?? "").slice(0, 30);
  return `finding-${index}-${title}-${summary}`;
}

function getCardState(
  err: ErrorItem,
  cardKey: string,
  inProgressKeys: Set<string>
): CardState {
  if (err?.pullRequestUrl) return "Completed";
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

import LogicResults from "@/components/LogicResults";
import UIResults from "@/components/UIResults";


export default function DashboardPage() {
  const [targetUrl, setTargetUrl] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"logic" | "ui">("logic");

  // Logic Agent State
  const [result, setResult] = useState<ScanResult | null>(null);
  const [streamingErrors, setStreamingErrors] = useState<ErrorItem[]>([]);
  const [selectedError, setSelectedError] = useState<ErrorItem | null>(null);
  const [selectedErrorKey, setSelectedErrorKey] = useState<string | null>(null);
  const [inProgressKeys, setInProgressKeys] = useState<string[]>([]);
  const inProgressSet = new Set(inProgressKeys);

  // UI Agent State
  const [uiLoading, setUiLoading] = useState(false);
  const [uiFindings, setUiFindings] = useState<UIResultItem[]>([]);

  const handleCreatePullRequest = async (err: ErrorItem, cardKey: string) => {
    setInProgressKeys((prev) => (prev.includes(cardKey) ? prev : [...prev, cardKey]));

    // For Logic findings, we might already have the modal open; for UI findings we definitely do.
    // We can keep the modal open or close it. User said "doesnt do anything", so let's keep it open or show feedback.
    // Actually, closing it and showing "In Progress" on the card is the existing pattern.
    setSelectedError(null);
    setSelectedErrorKey(null);

    try {
      const res = await fetch("/api/fix-workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          label: err.title,
          issue_summary: err.issueSummary,
          repo_full_name: githubRepo.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (data.ok && data.pr_url) {
        // Update both streaming and final results
        const updateFn = (prev: ErrorItem[]) =>
          prev.map((e) => (e.title === err.title ? { ...e, pullRequestUrl: data.pr_url } : e));

        setStreamingErrors(updateFn);
        if (result?.errors) {
          setResult({ ...result, errors: updateFn(result.errors) });
        }

        // Also update UI findings if it was a UI error
        if (err.status === "ui-error") {
          setUiFindings(prev => prev.map(f => {
            if (f.status === "bug" && f.content?.includes(err.title)) {
              // We can't easily store PR URL in f.content without parsing, 
              // but the modal logic uses the passed `err` object.
              // For now, the local state of results is updated which is enough for the tab views.
            }
            return f;
          }));
        }
      }
    } catch (e) {
      console.error("PR creation failed", e);
    } finally {
      setInProgressKeys((prev) => prev.filter((k) => k !== cardKey));
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
    setUiLoading(true);
    setResult(null);
    setStreamingErrors([]);
    setInProgressKeys([]);
    setUiFindings([]);

    const payload = {
      target_url: targetUrl.trim(),
      github_repo: githubRepo.trim() || undefined,
    };

    // Trigger Logic Agent (Streaming)
    const runLogicAnalysis = async () => {
      try {
        const res = await fetch("/api/run-scan/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok || !res.body) {
          const data = await res.json().catch(() => ({ message: "Failed to start analysis" }));
          setResult({ ok: false, summary: "", message: data.message, errors: [] });
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
                setStreamingErrors((prev) => [...prev, normalizeError(item.payload)]);
              } else if (item.type === "done") {
                const doneErrs = Array.isArray(item.errors) ? item.errors.map(normalizeError) : [];
                setResult({
                  ok: item.ok ?? false,
                  summary: item.summary ?? "",
                  message: item.message || `Found ${doneErrs.length} issue(s).`,
                  errors: doneErrs,
                });
              }
            } catch { }
          }
        }
      } catch (e: any) {
        setResult({ ok: false, summary: "", message: e.message, errors: [] });
      } finally {
        setLoading(false);
      }
    };

    // Trigger UI Agent (Streaming)
    const runUIAnalysis = async () => {
      try {
        const res = await fetch("/api/ui-analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok || !res.body) {
          const data = await res.json().catch(() => ({ message: "Failed" }));
          setUiFindings([{ status: "error", message: data.message }]);
          return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";
          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const item = JSON.parse(line.trim());
              setUiFindings((prev) => [...prev, item]);
              if (item.status === "done" || item.status === "error") break;
            } catch { }
          }
        }
      } catch (e: any) {
        setUiFindings([{ status: "error", message: e.message }]);
      } finally {
        setUiLoading(false);
      }
    };

    // Distribute concurrently
    Promise.all([runLogicAnalysis(), runUIAnalysis()]);
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
        {(result || loading || uiLoading || uiFindings.length > 0) && (
          <>
            <div className="tabs-header">
              <button
                className={`tab-btn ${activeTab === "logic" ? "active" : ""}`}
                onClick={() => setActiveTab("logic")}
              >
                Logic Agent
              </button>
              <button
                className={`tab-btn ${activeTab === "ui" ? "active" : ""}`}
                onClick={() => setActiveTab("ui")}
              >
                UI Agent
              </button>
            </div>

            {activeTab === "logic" ? (
              <LogicResults
                loading={loading}
                result={result}
                streamingErrors={streamingErrors}
                inProgressSet={inProgressSet}
                onSelectError={(err, key) => {
                  setSelectedError(err);
                  setSelectedErrorKey(key);
                }}
              />
            ) : (
              <UIResults
                loading={uiLoading}
                findings={uiFindings}
                onSelectError={(err, key) => {
                  setSelectedError(err);
                  setSelectedErrorKey(key);
                }}
              />
            )}
          </>
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
              {(() => {
                const modalKey = selectedErrorKey ?? `modal-${(selectedError.title ?? "").slice(0, 40)}`;
                // For UI errors, we don't track card state (Completed etc) yet
                const isUI = selectedError.status === "ui-error";
                const modalState = isUI ? "Error" : getCardState(selectedError, modalKey, inProgressSet);

                return (
                  <span className={`finding-modal-status finding-modal-status-${modalState.replace(/\s+/g, "-").toLowerCase()}`}>
                    {modalState}
                  </span>
                );
              })()}
              <h2 id="finding-modal-title" className="finding-modal-title">
                {selectedError.title}
              </h2>
              <div className="finding-modal-section">
                <h4 className="finding-modal-label">Summary</h4>
                <p className="finding-modal-summary">{selectedError.issueSummary || selectedError.description}</p>
              </div>
              {/* Removed redundant Description section for all agents as per user request */}
              {selectedError.pullRequestUrl && (
                <div className="finding-modal-section finding-modal-pr">
                  <h4 className="finding-modal-label">Pull request</h4>
                  <a
                    href={selectedError.pullRequestUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="finding-modal-pr-link"
                  >
                    View pull request →
                  </a>
                </div>
              )}
              <div className="finding-modal-actions">
                {selectedError.pullRequestUrl ? (
                  <a
                    href={selectedError.pullRequestUrl}
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
                  >
                    Create pull request
                  </button>
                )}
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
