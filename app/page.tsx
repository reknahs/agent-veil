import React from "react";
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="landing-logo">
          <span className="landing-logo-icon" aria-hidden />
          <span className="landing-logo-text">AgentVeil</span>
        </div>
        <div className="landing-nav-links">
          <Link href="/dashboard" className="landing-nav-link">
            Dashboard
          </Link>
          <Link href="#" className="landing-nav-link">
            Sign In
          </Link>
        </div>
      </nav>

      <main className="landing-hero">
        <div className="landing-hero-card">
          <h1 className="landing-headline">
            Automate feature delivery with your{" "}
            <span className="landing-highlight">community</span>
          </h1>
          <p className="landing-subtext">
            Capture the loudest signals, open issues, draft plans, and push PRs—without leaving your flow.
          </p>
          <div className="landing-actions">
            <Link href="/dashboard" className="landing-btn">
              VIEW DASHBOARD ↗
            </Link>
            <Link href="#" className="landing-btn">
              SIGN IN ↗
            </Link>
          </div>
        </div>
      </main>

      <footer className="landing-footer">
        <div className="landing-footer-n" aria-hidden>N</div>
        <div className="landing-footer-copy">© 2025 AgentVeil</div>
      </footer>
    </div>
  );
}
