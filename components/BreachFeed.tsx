"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";

const levelStyles: Record<string, string> = {
  info: "#a1a1aa",
  success: "#22c55e",
  warn: "#eab308",
  error: "#ef4444",
};

function formatTime(ts: number) {
  return new Date(ts).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function BreachFeed() {
  const logs = useQuery(api.queries.listLogs, { limit: 50 });

  if (logs === undefined) {
    return (
      <div className="breach-feed">
        <div className="breach-feed-header">Agent thoughts</div>
        <div className="breach-feed-loading">Loading…</div>
      </div>
    );
  }

  return (
    <div className="breach-feed">
      <div className="breach-feed-header">Agent thoughts</div>
      <div className="breach-feed-list">
        {logs.length === 0 ? (
          <div className="breach-feed-empty">
            No logs yet. Run &quot;Launch Attack&quot; to see activity.
          </div>
        ) : (
          logs.map((log) => (
            <div
              key={log._id}
              className="breach-feed-item"
              style={{
                borderLeftColor: levelStyles[log.level ?? "info"] ?? levelStyles.info,
              }}
            >
              <span className="breach-feed-time">{formatTime(log.timestamp)}</span>
              <span className="breach-feed-message">{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
