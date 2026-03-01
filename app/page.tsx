import React from "react";
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="landing">
      <div className="landing-bg">
        <div className="landing-bg-gradient" />
        <div className="landing-bg-grid" aria-hidden />
      </div>

      <nav className="landing-nav">
        <div className="landing-logo">
          <span className="landing-logo-icon" aria-hidden />
          <span className="landing-logo-text">AgentVeil</span>
        </div>
        <div className="landing-nav-links">
          <Link href="/dashboard" className="landing-nav-link">
            Dashboard
          </Link>
          <Link href="#" className="landing-nav-link landing-nav-cta">
            Sign In
          </Link>
        </div>
      </nav>

      <main className="landing-hero">
        <div className="landing-hero-card">
          <p className="landing-eyebrow">Security & delivery, automated</p>
          <h1 className="landing-headline">
            Fix website security misconfigurations in{" "}
            <span className="landing-highlight">minutes</span>
          </h1>
          <p className="landing-subtext">
            Capture the loudest signals, open issues, draft plans, and push PRs—without leaving your flow.
          </p>
          <div className="landing-actions">
            <Link href="/dashboard" className="landing-btn landing-btn-primary">
              View Dashboard
            </Link>
            <Link href="#" className="landing-btn landing-btn-secondary">
              Sign In
            </Link>
          </div>
        </div>
      </main>

      <footer className="landing-footer">
        <div className="landing-footer-copy">© 2025 AgentVeil</div>
      </footer>
    </div>
  );
}
