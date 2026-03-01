"use client";

import { useEffect } from "react";

function isConvexSyncError(message: string): boolean {
  return (
    message.includes("Could not find public function") ||
    message.includes("CONVEX Q(") ||
    message.includes("queries:getScanStatus") ||
    message.includes("queries:listWorkflows")
  );
}

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  const convexSync = isConvexSyncError(error.message);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        background: "#0f0f12",
        color: "#e4e4e7",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h2 style={{ marginBottom: "1rem", fontSize: "1.25rem" }}>
        {convexSync ? "Convex backend not synced" : "Something went wrong"}
      </h2>
      <p style={{ color: "#a1a1aa", marginBottom: "1.5rem", textAlign: "center", maxWidth: "420px" }}>
        {convexSync ? (
          <>
            The dashboard needs the latest Convex functions. From the project root run{" "}
            <code
              style={{
                background: "#27272a",
                padding: "0.125rem 0.375rem",
                borderRadius: "4px",
                fontSize: "0.875rem",
              }}
            >
              npx convex dev
            </code>{" "}
            or{" "}
            <code
              style={{
                background: "#27272a",
                padding: "0.125rem 0.375rem",
                borderRadius: "4px",
                fontSize: "0.875rem",
              }}
            >
              npx convex deploy
            </code>
            , then click Retry or refresh the page.
          </>
        ) : (
          error.message
        )}
      </p>
      <button
        onClick={reset}
        style={{
          padding: "0.5rem 1rem",
          background: convexSync ? "#0d9488" : "#dc2626",
          color: "white",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
          fontWeight: 600,
        }}
      >
        Try again
      </button>
    </div>
  );
}
