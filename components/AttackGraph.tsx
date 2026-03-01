"use client";

import { useQuery } from "convex/react";
import dynamic from "next/dynamic";
import { useMemo, useRef } from "react";
import { api } from "@/convex/_generated/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const DEFAULT_ROUTES = ["/", "/api/user", "/api/orders", "/api/auth", "/api/admin"];

// Stable graph structure so the force simulation never resets (nodes don't jump)
const STABLE_GRAPH = (() => {
  const nodes = DEFAULT_ROUTES.map((id) => ({ id, label: id }));
  const links = DEFAULT_ROUTES.filter((id) => id !== "/").map((target) => ({ source: "/", target }));
  return { nodes, links };
})();

export function AttackGraph() {
  const breaches = useQuery(api.queries.listBreaches);
  // Only show nodes as red for breaches that happened after this page loaded (so old demo data doesn’t show red immediately)
  const loadedAtRef = useRef<number>(Date.now());
  const breachedUrls = useMemo(
    () =>
      new Set(
        (breaches ?? [])
          .filter((b) => b.confirmedAt >= loadedAtRef.current)
          .map((b) => b.url)
      ),
    [breaches]
  );

  const nodeCanvasObject = useMemo(
    () =>
      (
        node: { id: string; x?: number; y?: number },
        ctx: CanvasRenderingContext2D,
        globalScale: number
      ) => {
        const label = String(node.id);
        const breached = breachedUrls.has(node.id);
        const fontSize = 12 / globalScale;
        ctx.font = `${fontSize}px sans-serif`;
        const padding = 4;
        const metrics = ctx.measureText(label);
        const w = metrics.width + padding * 2;
        const h = fontSize + padding * 2;
        const r = Math.max(w, h) / 2;

        ctx.beginPath();
        ctx.arc(node.x ?? 0, node.y ?? 0, r, 0, 2 * Math.PI);
        ctx.fillStyle = breached ? "#dc2626" : "#27272a";
        ctx.fill();
        ctx.strokeStyle = breached ? "#f87171" : "#3f3f46";
        ctx.lineWidth = 2 / globalScale;
        ctx.stroke();

        ctx.fillStyle = "#e4e4e7";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(label, node.x ?? 0, node.y ?? 0);
      },
    [breachedUrls]
  );

  return (
    <ForceGraph2D
      graphData={STABLE_GRAPH}
      nodeId="id"
      nodeCanvasObject={nodeCanvasObject}
      linkColor={() => "#3f3f46"}
      backgroundColor="#0f0f12"
      nodePointerAreaPaint={() => {}}
    />
  );
}
