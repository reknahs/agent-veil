"use client";

import React, { ReactNode } from "react";
import { ConvexProvider, ConvexReactClient } from "convex/react";

const convexUrl = process.env.NEXT_PUBLIC_CONVEX_URL;

const convex = convexUrl ? new ConvexReactClient(convexUrl) : null;

export function ConvexClientProvider({ children }: { children: ReactNode }) {
  if (!convex) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        fontFamily: "system-ui, sans-serif",
        background: "#0f0f12",
        color: "#e4e4e7",
      }}>
        <div style={{ maxWidth: "420px" }}>
          <h1 style={{ fontSize: "1.25rem", marginBottom: "0.5rem" }}>Convex URL missing</h1>
          <p style={{ color: "#a1a1aa", fontSize: "0.875rem", marginBottom: "1rem" }}>
            Add your Convex deployment URL to <code style={{ background: "#27272a", padding: "0.125rem 0.375rem", borderRadius: "4px" }}>.env.local</code>:
          </p>
          <pre style={{ background: "#18181b", padding: "1rem", borderRadius: "8px", fontSize: "0.8125rem", overflow: "auto" }}>
            NEXT_PUBLIC_CONVEX_URL=https://your-deployment.convex.cloud
          </pre>
          <p style={{ color: "#71717a", fontSize: "0.8125rem", marginTop: "1rem" }}>
            Get the URL from the Convex dashboard: your project → <strong>Settings</strong> → <strong>URL</strong>. Then restart <code>npm run dev:next</code>.
          </p>
        </div>
      </div>
    );
  }

  return <ConvexProvider client={convex}>{children}</ConvexProvider>;
}
