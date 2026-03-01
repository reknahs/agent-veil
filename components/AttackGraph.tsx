"use client";

import { useQuery } from "convex/react";
import dynamic from "next/dynamic";
import { useMemo } from "react";
import { api } from "@/convex/_generated/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const API_ROUTES = ["/", "/api/user", "/api/orders", "/api/auth", "/api/admin"];
const STATIC_SITE_ROUTES = ["/", "/about", "/research", "/projects", "/blogs", "/music"];

function getDefaultRoutes(targetUrl: string | undefined): string[] {
  if (!targetUrl || !targetUrl.trim()) return ["/"];
  const u = targetUrl.toLowerCase();
  if (u.includes("github.io") || u.includes("jayadevgh")) return STATIC_SITE_ROUTES;
  return API_ROUTES;
}

function pathFromUrl(url: string): string {
  if (url.startsWith("http")) {
    try {
      return new URL(url).pathname || "/";
    } catch {
      return url;
    }
  }
  return url;
}

export type BreachRecord = { url: string; type: string };

export function AttackGraph({
  targetUrl,
  onBreachSelect,
}: {
  targetUrl?: string;
  onBreachSelect?: (breach: BreachRecord) => void;
}) {
  const breaches = useQuery(api.queries.listBreaches);
  const defaultRoutes = useMemo(() => getDefaultRoutes(targetUrl), [targetUrl]);

  const { graphData, breachedUrls, breachByPath } = useMemo(() => {
    const breached = new Set<string>();
    const allRoutes = new Set<string>(defaultRoutes);
    const byPath = new Map<string, BreachRecord>();
    (breaches ?? []).forEach((b) => {
      const path = pathFromUrl(b.url);
      breached.add(path);
      breached.add(b.url);
      allRoutes.add(path);
      if (!byPath.has(path)) byPath.set(path, { url: b.url, type: b.type });
    });
    const nodes = Array.from(allRoutes).map((id) => ({ id, label: id }));
    const links = nodes
      .filter((n) => n.id !== "/")
      .map((target) => ({ source: "/", target }));
    return {
      graphData: { nodes, links },
      breachedUrls: breached,
      breachByPath: byPath,
    };
  }, [breaches, defaultRoutes]);

  const handleNodeClick = useMemo(() => {
    if (!onBreachSelect) return undefined;
    return (node: { id?: string | number }) => {
      const path = String(node.id ?? "");
      const breach = breachByPath.get(path);
      if (breach) onBreachSelect(breach);
    };
  }, [onBreachSelect, breachByPath]);

  const nodeCanvasObject = useMemo(
    () =>
      (
        node: { id?: string | number; x?: number; y?: number },
        ctx: CanvasRenderingContext2D,
        globalScale: number
      ) => {
        const label = String(node.id ?? "");
        const breached = breachedUrls.has(String(node.id ?? ""));
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

  const nodePointerAreaPaint = useMemo(
    () =>
      (
        node: { id?: string | number; x?: number; y?: number },
        color: string,
        ctx: CanvasRenderingContext2D,
        globalScale: number
      ) => {
        const label = String(node.id ?? "");
        const fontSize = 12 / globalScale;
        ctx.font = `${fontSize}px sans-serif`;
        const padding = 4;
        const metrics = ctx.measureText(label);
        const w = metrics.width + padding * 2;
        const h = fontSize + padding * 2;
        const r = Math.max(w, h) / 2;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(node.x ?? 0, node.y ?? 0, r, 0, 2 * Math.PI);
        ctx.fill();
      },
    []
  );

  return (
    <ForceGraph2D
      graphData={graphData}
      nodeId="id"
      nodeCanvasObject={nodeCanvasObject}
      nodePointerAreaPaint={nodePointerAreaPaint}
      onNodeClick={handleNodeClick}
      linkColor={() => "#3f3f46"}
      backgroundColor="#0f0f12"
    />
  );
}
