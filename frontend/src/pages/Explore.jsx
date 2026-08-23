import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import { GraphViewer } from "../components/GraphViewer";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Network, Info } from "lucide-react";

export default function Explore() {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [limit, setLimit] = useState(25);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.graphOverview(limit);
      setGraphData(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Network size={28} className="text-[#e94560]" />
            Graph Explorer
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Visual overview of the movie relationship graph. Click any node to navigate.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-400">Movies:</label>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="bg-[#1a1a2e] text-white border border-gray-700 rounded-lg px-3 py-2 text-sm
                       focus:outline-none focus:border-[#e94560]"
          >
            <option value={15}>15</option>
            <option value={25}>25</option>
            <option value={40}>40</option>
            <option value={60}>60</option>
          </select>
        </div>
      </div>

      {/* Info callout */}
      <div className="flex items-start gap-3 bg-[#16213e] border border-blue-900/50 rounded-xl p-4 text-sm text-gray-400">
        <Info size={16} className="text-blue-400 flex-shrink-0 mt-0.5" />
        <p>
          This graph is rendered from live CognoDB data using openCypher queries.
          Nodes are{" "}
          <span className="text-[#e94560]">Movies</span>,{" "}
          <span className="text-blue-400">Actors</span>, and{" "}
          <span className="text-yellow-400">Genres</span>.
          Edges represent ACTED_IN and IN_GENRE relationships traversed at query time.
        </p>
      </div>

      {loading && <LoadingState message="Loading graph data…" />}
      {error && <ErrorState message={error} onRetry={load} />}
      {!loading && !error && graphData && (
        <>
          <GraphViewer data={graphData} height={600} />
          <div className="flex gap-6 text-xs text-gray-500">
            <span>{graphData.nodes?.length || 0} nodes</span>
            <span>{graphData.links?.length || 0} relationships</span>
          </div>
        </>
      )}
    </div>
  );
}
