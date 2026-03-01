"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAction, useMutation, useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { AttackGraph, type WorkflowRecord } from "@/components/AttackGraph";
import { BreachDetailModal, type Breach } from "@/components/BreachDetailModal";
import { WorkflowDetailModal } from "@/components/WorkflowDetailModal";
import { BreachFeed } from "@/components/BreachFeed";

export default function DashboardPage() {
  const launchAttack = useAction(api.actions.launchAttack);
  const startWorkflowScan = useAction(api.actions.startWorkflowScan);
  const rebuildSecurity = useAction(api.actions.rebuildSecurity);
  const clearDemoData = useMutation(api.mutations.clearDemoData);
  const prStatus = useQuery(api.queries.getPrStatus);
  const scanStatus = useQuery(api.queries.getScanStatus);
  const [targetUrl, setTargetUrl] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [attacking, setAttacking] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [selectedBreach, setSelectedBreach] = useState<Breach | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowRecord | null>(null);
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

  const handleStartWorkflowScan = async () => {
    if (!targetUrl.trim() || !githubRepo.trim()) return;
    setScanning(true);
    try {
      await startWorkflowScan({
        target_url: targetUrl.trim(),
        github_repo: githubRepo.trim().replace(/^https?:\/\/github\.com\/?/, "").replace(/\/$/, ""),
      });
    } finally {
      setScanning(false);
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

  const canLaunch = targetUrl.trim().length > 0;
  const canStartScan = targetUrl.trim().length > 0 && githubRepo.trim().length > 0;
  const scanInProgress = scanStatus?.status === "running" || scanStatus?.status === "pending";

  const handleReset = async () => {
    setResetting(true);
    setSelectedBreach(null);
    setSelectedWorkflow(null);
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
            onClick={handleStartWorkflowScan}
            disabled={scanning || !canStartScan || scanInProgress}
            title={!canStartScan ? "Enter Target URL and GitHub Repo" : scanInProgress ? "Scan in progress" : undefined}
          >
            {scanning ? "Starting…" : scanInProgress ? "Scan running…" : "Start workflow scan"}
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
            {scanStatus?.status === "running" || scanStatus?.status === "pending"
              ? "Workflow scan in progress…"
              : "Click a node: red = issue, black = OK. Click for details."}
          </p>
          <div className="graph-container">
            <AttackGraph
              targetUrl={targetUrl}
              onBreachSelect={setSelectedBreach}
              onWorkflowSelect={setSelectedWorkflow}
            />
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
        />
      )}
    </div>
  );
}
