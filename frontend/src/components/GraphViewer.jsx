import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";

const NODE_COLORS = {
  Movie: "#e94560",
  Actor: "#3b82f6",
  Director: "#10b981",
  Genre: "#f59e0b",
};

export function GraphViewer({ data, height = 500 }) {
  const containerRef = useRef(null);
  const graphRef = useRef(null);
  const navigate = useNavigate();
  const [ForceGraph, setForceGraph] = useState(null);
  const [tooltip, setTooltip] = useState(null);

  // Dynamically import (it uses browser APIs)
  useEffect(() => {
    import("react-force-graph-2d").then((mod) => setForceGraph(() => mod.default));
  }, []);

  const handleNodeClick = useCallback(
    (node) => {
      if (node.type === "Movie") navigate(`/movie/${encodeURIComponent(node.label)}`);
      else if (node.type === "Actor") navigate(`/actor/${encodeURIComponent(node.label)}`);
    },
    [navigate]
  );

  const handleNodeHover = useCallback((node) => {
    setTooltip(node ? { label: node.label, type: node.type } : null);
  }, []);

  if (!ForceGraph) {
    return (
      <div
        className="flex items-center justify-center rounded-xl bg-[#16213e] border border-gray-700"
        style={{ height }}
      >
        <div className="w-8 h-8 border-4 border-[#e94560] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div
      className="relative rounded-xl overflow-hidden border border-gray-700 bg-[#0d0d0d]"
      style={{ height }}
    >
      {tooltip && (
        <div className="absolute top-3 left-3 z-10 bg-[#1a1a2e] border border-gray-700 rounded-lg px-3 py-2 pointer-events-none">
          <span
            className="text-xs font-bold mr-2 px-2 py-0.5 rounded-full"
            style={{ background: NODE_COLORS[tooltip.type] + "33", color: NODE_COLORS[tooltip.type] }}
          >
            {tooltip.type}
          </span>
          <span className="text-sm text-white">{tooltip.label}</span>
        </div>
      )}

      {/* Legend */}
      <div className="absolute top-3 right-3 z-10 bg-[#1a1a2e]/90 border border-gray-700 rounded-lg p-2 flex flex-col gap-1">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: color }} />
            <span className="text-xs text-gray-400">{type}</span>
          </div>
        ))}
      </div>

      <ForceGraph
        ref={graphRef}
        graphData={{
          nodes: (data?.nodes || []).map((n) => ({ ...n, id: n.id })),
          links: (data?.links || []).map((l) => ({ source: l.source, target: l.target, label: l.label })),
        }}
        width={containerRef.current?.offsetWidth || 800}
        height={height}
        backgroundColor="#0d0d0d"
        nodeLabel="label"
        nodeColor={(n) => NODE_COLORS[n.type] || "#888"}
        nodeRelSize={6}
        linkColor={() => "#374151"}
        linkWidth={1.5}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const label = node.label;
          const fontSize = Math.max(10 / globalScale, 3);
          const r = 6;
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
          ctx.fillStyle = NODE_COLORS[node.type] || "#888";
          ctx.fill();
          if (globalScale >= 1.5) {
            ctx.font = `${fontSize}px Inter, sans-serif`;
            ctx.fillStyle = "rgba(255,255,255,0.85)";
            ctx.textAlign = "center";
            ctx.fillText(label, node.x, node.y + r + fontSize);
          }
        }}
      />
    </div>
  );
}
