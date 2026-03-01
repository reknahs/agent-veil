"use client";

import React from "react";

export type WorkflowRecord = {
  _id: string;
  label: string;
  status: "pending" | "ok" | "has_issue";
  issue_summary?: string;
  steps?: string[];
  step_count?: number;
};

export function WorkflowDetailModal({
  workflow,
  onClose,
}: {
  workflow: WorkflowRecord;
  onClose: () => void;
}) {
  const steps = workflow.steps ?? [];
  const hasIssue = workflow.status === "has_issue";

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Workflow</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className="modal-body">
          <div
            className={
              hasIssue ? "modal-badge modal-badge-breach" : "modal-badge"
            }
            style={hasIssue ? undefined : { background: "rgba(34, 197, 94, 0.2)", color: "#22c55e" }}
          >
            {workflow.status === "pending"
              ? "Pending"
              : hasIssue
                ? "Issue"
                : "OK"}
          </div>
          <p className="modal-url" style={{ marginBottom: "0.5rem" }}>
            {workflow.label}
          </p>
          {workflow.issue_summary && (
            <>
              <h4 className="modal-section-title">Issue</h4>
              <p className="modal-explanation">{workflow.issue_summary}</p>
            </>
          )}
          <h4 className="modal-section-title">Steps ({steps.length})</h4>
          {steps.length > 0 ? (
            <ol style={{ margin: 0, paddingLeft: "1.25rem", color: "#a1a1aa", fontSize: "0.9375rem", lineHeight: 1.6 }}>
              {steps.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ol>
          ) : (
            <p className="modal-explanation">No steps recorded.</p>
          )}
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
