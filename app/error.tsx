"use client";

import { useEffect } from "react";

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

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "2rem",
      background: "#0f0f12",
      color: "#e4e4e7",
      fontFamily: "system-ui, sans-serif",
    }}>
      <h2 style={{ marginBottom: "1rem", fontSize: "1.25rem" }}>Something went wrong</h2>
      <p style={{ color: "#a1a1aa", marginBottom: "1.5rem", textAlign: "center" }}>
        {error.message}
      </p>
      <button
        onClick={reset}
        style={{
          padding: "0.5rem 1rem",
          background: "#dc2626",
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
