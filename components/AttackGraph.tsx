"use client";

import { useQuery } from "convex/react";
import dynamic from "next/dynamic";
import { useMemo } from "react";
import { api } from "@/convex/_generated/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const DEFAULT_ROUTES = ["/", "/api/user", "/api/orders", "/api/auth", "/api/admin"];

export function AttackGraph() {
  const breaches = useQuery(api.queries.listBreaches);

  const graphData = useMemo(() => {
    const breachedUrls = new Set((breaches ?? []).map((b) => b.url));
    const allUrls = Array.from(new Set([...DEFAULT_ROUTES, ...breachedUrls]));
    const nodes = allUrls.map((id) => ({
      id,
      label: id,
      breached: breachedUrls.has(id),
    }));
    const links: { source: string; target: string }[] = [];
    const root = "/";
    allUrls.filter((u) => u !== root).forEach((target) => {
      links.push({ source: root, target });
    });
    return { nodes, links };
  }, [breaches]);

  const nodeCanvasObject = useMemo(
    () =>
      (
        node: any,
        ctx: CanvasRenderingContext2D,
        globalScale: number
      ) => {
        const label = String(node.id);
        const breached = "breached" in node && node.breached;
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
    []
  );

  if (graphData.nodes.length === 0) {
    return (
      <div className="graph-placeholder">
        <p>No routes yet. Run &quot;Launch Attack&quot; to see the graph.</p>
      </div>
    );
  }

  return (
    <ForceGraph2D
      graphData={graphData}
      nodeId="id"
      nodeCanvasObject={nodeCanvasObject}
      linkColor={() => "#3f3f46"}
      backgroundColor="#0f0f12"
      nodePointerAreaPaint={() => { }}
    />
  );
}
