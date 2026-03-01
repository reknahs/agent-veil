import React from "react";
import Link from "next/link";
import { SecurityHeroGraphic } from "@/components/SecurityHeroGraphic";

export default function HomePage() {
  return (
    <div className="landing landing-hoobank">
      <div className="landing-bg">
        <div className="landing-bg-gradient" />
        <div className="landing-bg-grid" aria-hidden />
        {/* HooBank-style blur gradients for depth */}
        <div className="landing-bg-blur landing-bg-blur-teal" />
        <div className="landing-bg-blur landing-bg-blur-green" />
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

      <main className="landing-hero landing-hero-split">
        <div className="landing-hero-left">
          {/* HooBank-style discount / promo pill */}
          <div className="landing-pill">
            <span className="landing-pill-icon" aria-hidden>✓</span>
            <span>Fix security in minutes — no code required</span>
          </div>
          <h1 className="landing-headline">
            The next generation{" "}
            <span className="landing-highlight landing-highlight-teal">security</span>
            {" "}for your site
          </h1>
          <p className="landing-subtext">
            Capture the loudest signals, open issues, draft plans, and push PRs—without leaving your flow. Fix website misconfigurations in minutes.
          </p>
          <div className="landing-actions">
            <Link href="/dashboard" className="landing-btn landing-btn-cta">
              <span>Get Started</span>
              <span className="landing-btn-arrow" aria-hidden>→</span>
            </Link>
            <Link href="#" className="landing-btn landing-btn-secondary">
              Sign In
            </Link>
          </div>
        </div>
        <div className="landing-hero-right">
          <SecurityHeroGraphic />
        </div>
      </main>

      <footer className="landing-footer">
        <div className="landing-footer-copy">© 2025 AgentVeil</div>
      </footer>
    </div>
  );
}
