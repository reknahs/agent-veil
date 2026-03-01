"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAction, useMutation, useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { AttackGraph, type WorkflowRecord } from "@/components/AttackGraph";
import { BreachDetailModal, type Breach } from "@/components/BreachDetailModal";
import { WorkflowDetailModal } from "@/components/WorkflowDetailModal";
import { AgentErrorDetailModal, type AgentErrorRecord } from "@/components/AgentErrorDetailModal";
import { BreachFeed } from "@/components/BreachFeed";

export default function DashboardPage() {
  const launchAttack = useAction(api.actions.launchAttack);
  const seedDemoWorkflows = useMutation(api.mutations.seedDemoWorkflows);
  const rebuildSecurity = useAction(api.actions.rebuildSecurity);
  const createFixPrForWorkflow = useAction(api.actions.createFixPrForWorkflow);
  const startAgentScan = useAction(api.actions.startAgentScan);
  const clearDemoData = useMutation(api.mutations.clearDemoData);
  const prStatus = useQuery(api.queries.getPrStatus);
  const agentErrors = useQuery(api.queries.listAgentErrors, { limit: 50 });
  const [targetUrl, setTargetUrl] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [attacking, setAttacking] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const [workflowFixLoading, setWorkflowFixLoading] = useState(false);
  const [agentScanLoading, setAgentScanLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [selectedBreach, setSelectedBreach] = useState<Breach | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowRecord | null>(null);
  const [selectedAgentError, setSelectedAgentError] = useState<AgentErrorRecord | null>(null);
  const hasClearedOnMount = useRef(false);

  useEffect(() => {
    if (hasClearedOnMount.current) return;
    hasClearedOnMount.current = true;
    clearDemoData({});
  }, [clearDemoData]);

  const handleLaunchAttack = async () => {
    if (!targetUrl.trim()) return;
    setAttacking(true);
    try {
      await launchAttack({ demo: true, target_url: targetUrl.trim() });
    } finally {
      setAttacking(false);
    }
  };

  const handleLoadDemoGraph = async () => {
    setLoadingDemo(true);
    try {
      await seedDemoWorkflows({});
    } finally {
      setLoadingDemo(false);
    }
  };

  const handleRebuild = async (singleBreach?: Breach) => {
    setRebuilding(true);
    try {
      await rebuildSecurity({
        github_repo: githubRepo.trim() ? githubRepo.trim() : undefined,
        single_breach: singleBreach,
      });
      if (singleBreach) setSelectedBreach(null);
    } finally {
      setRebuilding(false);
    }
  };

  const handleCreateFixPrForWorkflow = async (workflow: WorkflowRecord) => {
    if (!workflow.issue_summary) return;
    setWorkflowFixLoading(true);
    try {
      await createFixPrForWorkflow({
        workflow_id: workflow._id,
        label: workflow.label,
        issue_summary: workflow.issue_summary,
        github_repo: githubRepo.trim() ? githubRepo.trim() : undefined,
      });
    } finally {
      setWorkflowFixLoading(false);
    }
  };

  const handleCreateFixPrForAgentError = async (err: AgentErrorRecord) => {
    setWorkflowFixLoading(true);
    try {
      await createFixPrForWorkflow({
        label: err.title,
        issue_summary: err.issueSummary,
        github_repo: githubRepo.trim() ? githubRepo.trim() : undefined,
      });
    } finally {
      setWorkflowFixLoading(false);
    }
  };

  const handleRunAgentScan = async () => {
    if (!targetUrl.trim()) return;
    setAgentScanLoading(true);
    try {
      await startAgentScan({ target_url: targetUrl.trim() });
    } finally {
      setAgentScanLoading(false);
    }
  };

  const canLaunch = targetUrl.trim().length > 0;

  const handleReset = async () => {
    setResetting(true);
    setSelectedBreach(null);
    setSelectedWorkflow(null);
    setSelectedAgentError(null);
    try {
      await clearDemoData({});
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="dashboard-header-top">
          <div className="dashboard-title-block">
            <h1>Security Cartographer</h1>
            <p className="dashboard-tagline">Live attack graph & breach feed</p>
          </div>
        </div>

        <div className="dashboard-target-row">
          <label htmlFor="target-url" className="target-label">
            Target URL
          </label>
          <input
            id="target-url"
            type="url"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            placeholder="https://jayadevgh.github.io"
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
            placeholder="owner/repo (e.g. jayadevgh/jayadevgh.github.io)"
            className="target-input"
          />
          <button
            type="button"
            className="btn btn-ghost"
            onClick={handleReset}
            disabled={resetting}
            title="Clear breaches, logs, and reset graph"
          >
            {resetting ? "Resetting…" : "Reset"}
          </button>
        </div>

        <div className="dashboard-actions">
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleLoadDemoGraph}
            disabled={loadingDemo}
            title="Load a predetermined graph with red (issue) and black (ok) workflow nodes for testing"
          >
            {loadingDemo ? "Loading…" : "Load demo graph"}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleLaunchAttack}
            disabled={attacking || !canLaunch}
            title={!canLaunch ? "Enter Target URL first" : undefined}
          >
            {attacking ? "Running…" : "Launch Attack (demo)"}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => handleRebuild()}
            disabled={rebuilding}
          >
            {rebuilding ? "Creating PR…" : "Rebuild Security"}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleRunAgentScan}
            disabled={agentScanLoading || !targetUrl.trim()}
            title="Run agent to find issues on the target site; results appear in Agent findings below"
          >
            {agentScanLoading ? "Running agent…" : "Run agent scan"}
          </button>
        </div>

        {prStatus && (prStatus.pr_url || prStatus.message) && (
          <p className="dashboard-pr-status">
            {prStatus.pr_url ? (
              <>
                PR:{" "}
                <a href={prStatus.pr_url} target="_blank" rel="noopener noreferrer" className="pr-link">
                  {prStatus.pr_url}
                </a>
                {prStatus.message && <span className="pr-message"> — {prStatus.message}</span>}
              </>
            ) : (
              <span className="pr-message">{prStatus.message}</span>
            )}
          </p>
        )}
      </header>

      <main className="dashboard-main">
        <section className="dashboard-graph">
          <h2>Attack graph</h2>
          <p className="dashboard-graph-hint">
            Click &quot;Load demo graph&quot; to show workflow nodes. Red = issue, black = OK. Click a node for details.
          </p>
          <div className="graph-container">
            <AttackGraph
              targetUrl={targetUrl}
              onBreachSelect={setSelectedBreach}
              onWorkflowSelect={setSelectedWorkflow}
            />
          </div>
          <div className="agent-findings">
            <div className="agent-findings-header">
              <h3 className="agent-findings-title">Agent findings</h3>
              {agentErrors && agentErrors.length > 0 && (
                <span className="agent-findings-title">{agentErrors.length} issue(s)</span>
              )}
            </div>
            {agentErrors == null ? (
              <p className="agent-findings-empty">Loading…</p>
            ) : agentErrors.length === 0 ? (
              <p className="agent-findings-empty">
                Enter a website URL and GitHub repo, then click &quot;Run agent scan&quot; to find issues. Each finding appears as a card; click for details and &quot;Fix PR request&quot;.
              </p>
            ) : (
              <div className="agent-findings-grid">
                {agentErrors.map((err) => (
                  <button
                    key={err._id}
                    type="button"
                    className="agent-finding-card"
                    onClick={() => setSelectedAgentError(err)}
                  >
                    <span className="agent-finding-tag">Issue</span>
                    <h4 className="agent-finding-title">{err.title}</h4>
                    <p className="agent-finding-description">{err.issueSummary}</p>
                    <p className="agent-finding-meta">
                      Last: {new Date(err.createdAt).toLocaleString()}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </section>

        <aside className="dashboard-feed">
          <BreachFeed />
        </aside>
      </main>

      {selectedBreach && (
        <BreachDetailModal
          breach={selectedBreach}
          onClose={() => setSelectedBreach(null)}
          onCreateFixPR={() => handleRebuild(selectedBreach)}
          loading={rebuilding}
        />
      )}
      {selectedWorkflow && (
        <WorkflowDetailModal
          workflow={{
            _id: selectedWorkflow._id,
            label: selectedWorkflow.label,
            status: selectedWorkflow.status,
            issue_summary: selectedWorkflow.issue_summary,
            steps: selectedWorkflow.steps,
            step_count: selectedWorkflow.step_count,
          }}
          onClose={() => setSelectedWorkflow(null)}
          onCreateFixPR={() => handleCreateFixPrForWorkflow(selectedWorkflow)}
          loading={workflowFixLoading}
        />
      )}
      {selectedAgentError && (
        <AgentErrorDetailModal
          error={selectedAgentError}
          onClose={() => setSelectedAgentError(null)}
          onCreateFixPR={() => handleCreateFixPrForAgentError(selectedAgentError)}
          loading={workflowFixLoading}
        />
      )}
    </div>
  );
}
