"use client";

import React from "react";
import { useAction } from "convex/react";
import { api } from "@/convex/_generated/api";
import { AttackGraph } from "@/components/AttackGraph";
import { BreachFeed } from "@/components/BreachFeed";

export default function DashboardPage() {
  const launchAttack = useAction(api.actions.launchAttack);
  const rebuildSecurity = useAction(api.actions.rebuildSecurity);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Security Cartographer</h1>
        <p className="dashboard-tagline">Live attack graph & breach feed</p>
        <div className="dashboard-actions">
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => launchAttack({ demo: true })}
          >
            Launch Attack
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => rebuildSecurity({})}
          >
            Rebuild Security
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <section className="dashboard-graph">
          <h2>Attack graph</h2>
          <div className="graph-container">
            <AttackGraph />
          </div>
        </section>

        <aside className="dashboard-feed">
          <BreachFeed />
        </aside>
      </main>
    </div>
  );
}
