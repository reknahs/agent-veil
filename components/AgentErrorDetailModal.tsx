"use client";

import React from "react";
import type { Id } from "@/convex/_generated/dataModel";

export type AgentErrorRecord = {
  _id: Id<"agent_errors">;
  targetUrl?: string;
  title: string;
  issueSummary: string;
  description?: string;
  status?: string;
  taskId?: string;
  createdAt: number;
};

export function AgentErrorDetailModal({
  error: agentError,
  onClose,
  onCreateFixPR,
  loading,
}: {
  error: AgentErrorRecord;
  onClose: () => void;
  onCreateFixPR?: () => void;
  loading?: boolean;
}) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Agent finding</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className="modal-body">
          <div className="modal-badge modal-badge-breach">ISSUE</div>
          <p className="modal-url" style={{ marginBottom: "0.5rem" }}>
            {agentError.title}
          </p>
          <h4 className="modal-section-title">Issue</h4>
          <p className="modal-explanation">{agentError.issueSummary}</p>
          {agentError.description && (
            <>
              <h4 className="modal-section-title">Details</h4>
              <p className="modal-explanation" style={{ whiteSpace: "pre-wrap", fontSize: "0.875rem" }}>
                {agentError.description.slice(0, 1500)}
                {agentError.description.length > 1500 ? "…" : ""}
              </p>
            </>
          )}
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Close
          </button>
          {onCreateFixPR && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={onCreateFixPR}
              disabled={loading}
            >
              {loading ? "Creating PR…" : "Fix PR request"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
