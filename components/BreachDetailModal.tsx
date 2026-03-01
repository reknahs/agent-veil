"use client";

import React from "react";

const BREACH_EXPLANATIONS: Record<string, { title: string; explanation: string; fix: string }> = {
  IDOR: {
    title: "Insecure Direct Object Reference (IDOR)",
    explanation:
      "The application allows access to other users' data by changing the ID in the URL (e.g. id=101 → id=102). An attacker can enumerate IDs to access unauthorized resources. The server does not verify that the requesting user is authorized to access the requested object.",
    fix: "Add authorization checks that validate the user has permission to access the requested resource. Use server-side validation and never trust client-supplied IDs alone.",
  },
  "Auth Bypass": {
    title: "Authentication Bypass",
    explanation:
      "Sensitive data or authenticated pages remain accessible after logout (e.g. via browser Back button). Session state is not properly invalidated, so cached content or stale tokens can still be viewed. This allows a shared-device attacker to see previous user data.",
    fix: "Invalidate sessions on logout (clear tokens, mark session as expired). Add Cache-Control: no-store for sensitive pages. Use proper redirects after logout.",
  },
  "Missing Headers": {
    title: "Missing Security Headers",
    explanation:
      "The response lacks Content-Security-Policy (CSP), X-Frame-Options, or X-Content-Type-Options. This increases risk of XSS, clickjacking, and MIME-sniffing attacks. Browsers may interpret content in unsafe ways without these headers.",
    fix: "Add headers in your server or middleware: Content-Security-Policy, X-Frame-Options: DENY, X-Content-Type-Options: nosniff.",
  },
  "Server Error": {
    title: "Server Error Exposure",
    explanation:
      "The server returned a 5xx error, which may leak stack traces or internal paths. Production servers should return generic error pages and log details server-side.",
    fix: "Return generic error pages to clients. Log full error details server-side. Avoid exposing stack traces or file paths in responses.",
  },
  "Cookie Leaks": {
    title: "Cookie / Session Leak",
    explanation:
      "Cookies or session data may be exposed to unauthorized parties via console errors, network inspection, or improper SameSite/Secure attributes. Sensitive tokens could be logged or transmitted insecurely.",
    fix: "Use HttpOnly, Secure, and SameSite=Strict for sensitive cookies. Never log or expose tokens to the client.",
  },
};

const defaultExplanation = {
  title: "Security Breach",
  explanation: "A security vulnerability was detected at this endpoint. The exact nature depends on the scan results.",
  fix: "Review the endpoint for common vulnerabilities: authorization checks, input validation, and secure headers.",
};

export type Breach = { url: string; type: string };

export function BreachDetailModal({
  breach,
  onClose,
  onCreateFixPR,
  loading,
}: {
  breach: Breach;
  onClose: () => void;
  onCreateFixPR: () => void;
  loading: boolean;
}) {
  const info = BREACH_EXPLANATIONS[breach.type] ?? defaultExplanation;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Breach Details</h3>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className="modal-body">
          <div className="modal-badge modal-badge-breach">{breach.type}</div>
          <p className="modal-url">{breach.url}</p>
          <h4 className="modal-section-title">{info.title}</h4>
          <p className="modal-explanation">{info.explanation}</p>
          <h4 className="modal-section-title">How to fix</h4>
          <p className="modal-fix">{info.fix}</p>
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Close
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={onCreateFixPR}
            disabled={loading}
          >
            {loading ? "Creating PR…" : "Create Fix PR"}
          </button>
        </div>
      </div>
    </div>
  );
}
