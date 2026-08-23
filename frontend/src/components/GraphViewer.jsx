import { useEffect, useRef, useState, useCallback, useMemo } from "react";
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
  const [hoverNode, setHoverNode] = useState(null);

  useEffect(() => {
    import("react-force-graph-2d").then((mod) => setForceGraph(() => mod.default));
  }, []);

  // Memoize graph data so we can calculate highlights
  const graphData = useMemo(() => {
    return {
      nodes: (data?.nodes || []).map((n) => ({ ...n, id: n.id })),
      links: (data?.links || []).map((l) => ({ source: l.source, target: l.target, label: l.label })),
    };
  }, [data]);

  // Calculate which nodes and links to highlight when hovering
  const { highlightNodes, highlightLinks } = useMemo(() => {
    const nodes = new Set();
    const links = new Set();
    if (hoverNode) {
      nodes.add(hoverNode.id);
      graphData.links.forEach((link) => {
        // react-force-graph mutates source/target into objects after initialization
        const sourceId = typeof link.source === "object" ? link.source.id : link.source;
        const targetId = typeof link.target === "object" ? link.target.id : link.target;
        
        if (sourceId === hoverNode.id || targetId === hoverNode.id) {
          links.add(link);
          nodes.add(sourceId);
          nodes.add(targetId);
        }
      });
    }
    return { highlightNodes: nodes, highlightLinks: links };
  }, [hoverNode, graphData]);

  const handleNodeClick = useCallback(
    (node) => {
      if (node.type === "Movie") navigate(`/movie/${encodeURIComponent(node.label)}`);
      else if (node.type === "Actor") navigate(`/actor/${encodeURIComponent(node.label)}`);
    },
    [navigate]
  );

  const handleNodeHover = useCallback((node) => {
    // If we hover over the canvas but not a node, node is null.
    // We update the state to trigger highlight calculation.
    setHoverNode(node || null);
    
    // Change cursor
    if (containerRef.current) {
      containerRef.current.style.cursor = node ? "pointer" : "default";
    }
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
      ref={containerRef}
      className="relative rounded-xl overflow-hidden border border-gray-700 bg-[#0d0d0d]"
      style={{ height }}
    >
      {/* Dynamic Hover Tooltip - Top Left */}
      {hoverNode && (
        <div className="absolute top-3 left-3 z-10 bg-[#1a1a2e]/95 border border-gray-700 rounded-lg px-3 py-2 pointer-events-none shadow-lg">
          <span
            className="text-xs font-bold mr-2 px-2 py-0.5 rounded-full"
            style={{ background: NODE_COLORS[hoverNode.type] + "33", color: NODE_COLORS[hoverNode.type] }}
          >
            {hoverNode.type}
          </span>
          <span className="text-sm text-white font-medium">{hoverNode.label}</span>
          
          {/* Show a hint to click if it's a clickable node */}
          {(hoverNode.type === "Movie" || hoverNode.type === "Actor") && (
            <p className="text-[10px] text-gray-400 mt-1 pt-1 border-t border-gray-700">
              Click to view details
            </p>
          )}
        </div>
      )}

      {/* Legend - Top Right */}
      <div className="absolute top-3 right-3 z-10 bg-[#1a1a2e]/90 border border-gray-700 rounded-lg p-2 flex flex-col gap-1 pointer-events-none shadow-lg">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: color }} />
            <span className="text-xs text-gray-300 font-medium">{type}</span>
          </div>
        ))}
      </div>

      <ForceGraph
        ref={graphRef}
        graphData={graphData}
        width={containerRef.current?.offsetWidth || 800}
        height={height}
        backgroundColor="#0d0d0d"
        // We explicitly remove nodeLabel so the default ugly browser tooltip doesn't appear
        nodeColor={(n) => NODE_COLORS[n.type] || "#888"}
        nodeRelSize={6}
        
        // Link styling: dim links that aren't connected to the hovered node
        linkColor={(link) => 
          hoverNode && !highlightLinks.has(link) ? "#ffffff11" : "#4b5563"
        }
        linkWidth={(link) => (highlightLinks.has(link) ? 2 : 1)}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkDirectionalArrowColor={(link) => 
          hoverNode && !highlightLinks.has(link) ? "#ffffff11" : "#4b5563"
        }
        
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
        
        // Custom canvas rendering for nodes
        nodeCanvasObject={(node, ctx, globalScale) => {
          const isHovered = hoverNode?.id === node.id;
          const isHighlighted = highlightNodes.has(node.id);
          const isDimmed = hoverNode && !isHighlighted;
          
          const label = node.label;
          const fontSize = isHovered ? 12 / globalScale : Math.max(10 / globalScale, 3);
          const r = isHovered ? 8 : 6;
          
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
          
          // Apply dimming logic
          ctx.fillStyle = isDimmed 
            ? "#ffffff11" 
            : (NODE_COLORS[node.type] || "#888");
          ctx.fill();
          
          // Draw text label if zoomed in, or if it's specifically highlighted
          if (!isDimmed && (globalScale >= 1.5 || isHighlighted)) {
            ctx.font = `${isHovered ? "bold " : ""}${fontSize}px Inter, sans-serif`;
            ctx.fillStyle = isHovered ? "#ffffff" : "rgba(255,255,255,0.7)";
            ctx.textAlign = "center";
            ctx.textBaseline = "top";
            
            // Add a small background box behind the text to make it readable over links
            if (isHovered || isHighlighted) {
              const textWidth = ctx.measureText(label).width;
              ctx.fillStyle = "rgba(13, 13, 13, 0.7)";
              ctx.fillRect(node.x - textWidth/2 - 2, node.y + r + 2, textWidth + 4, fontSize + 4);
              ctx.fillStyle = isHovered ? "#ffffff" : "rgba(255,255,255,0.9)";
            }
            
            ctx.fillText(label, node.x, node.y + r + 4);
          }
        }}
      />
    </div>
  );
}
