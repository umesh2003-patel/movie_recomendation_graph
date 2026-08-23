import { useParams } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import { MovieCard } from "../components/MovieCard";
import { ActorCard } from "../components/ActorCard";
import { GraphViewer } from "../components/GraphViewer";
import { LoadingState, ErrorState, EmptyState } from "../components/LoadingState";
import { Star, Calendar, Film, Network } from "lucide-react";

const FALLBACK_POSTER = "https://via.placeholder.com/300x450/1a1a2e/e94560?text=No+Poster";

export default function MovieDetail() {
  const { title } = useParams();
  const decodedTitle = decodeURIComponent(title);

  const [movie, setMovie] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("cast"); // cast | graph | recommend

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, recs, graph] = await Promise.all([
        api.getMovie(decodedTitle),
        api.recommendForMovie(decodedTitle),
        api.movieGraph(decodedTitle),
      ]);
      setMovie(m);
      setRecommendations(recs);
      setGraphData(graph);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [decodedTitle]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingState message="Loading movie…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!movie) return <EmptyState message="Movie not found." />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row gap-8">
        <img
          src={movie.poster_url || FALLBACK_POSTER}
          alt={movie.title}
          onError={(e) => { e.target.src = FALLBACK_POSTER; }}
          className="w-48 md:w-64 rounded-2xl object-cover self-start flex-shrink-0 shadow-2xl border border-gray-700"
        />
        <div className="space-y-4 flex-1">
          <div className="flex flex-wrap gap-2">
            {movie.genres?.map((g) => (
              <span key={g} className="px-3 py-1 bg-[#e94560]/10 text-[#e94560] text-xs font-medium rounded-full border border-[#e94560]/30">
                {g}
              </span>
            ))}
          </div>
          <h1 className="text-4xl font-bold text-white">{movie.title}</h1>
          {movie.tagline && <p className="text-gray-400 italic text-lg">"{movie.tagline}"</p>}
          <div className="flex flex-wrap items-center gap-6 text-sm text-gray-400">
            {movie.year && (
              <span className="flex items-center gap-1.5">
                <Calendar size={14} /> {movie.year}
              </span>
            )}
            {movie.rating && (
              <span className="flex items-center gap-1.5 text-[#f5c518]">
                <Star size={14} className="fill-[#f5c518]" />
                <span className="font-bold">{movie.rating.toFixed(1)}</span>
                <span className="text-gray-500">/ 10</span>
              </span>
            )}
            {movie.directors?.length > 0 && (
              <span className="flex items-center gap-1.5">
                <Film size={14} />
                Directed by <strong className="text-white ml-1">{movie.directors.join(", ")}</strong>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-800">
        {[
          { id: "cast", label: `Cast (${movie.cast?.length || 0})` },
          { id: "graph", label: "Graph View" },
          { id: "recommend", label: "You Might Like" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === t.id
                ? "border-[#e94560] text-[#e94560]"
                : "border-transparent text-gray-500 hover:text-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === "cast" && (
        <div>
          {movie.cast?.length === 0 ? (
            <EmptyState message="No cast information available." icon="🎭" />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {movie.cast?.map((c) => (
                <ActorCard
                  key={c.name}
                  actor={{ name: c.name, born: c.born, role: c.role }}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "graph" && (
        <div className="space-y-3">
          <p className="text-gray-400 text-sm flex items-center gap-2">
            <Network size={14} className="text-[#e94560]" />
            Interactive graph — click any node to navigate. Scroll to zoom.
          </p>
          <GraphViewer data={graphData} height={520} />
        </div>
      )}

      {tab === "recommend" && (
        <div>
          {recommendations.length === 0 ? (
            <EmptyState message="No recommendations found." icon="🎬" />
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {recommendations.map((r) => (
                <MovieCard key={r.title} movie={{ title: r.title, year: r.year, rating: r.rating, poster_url: r.poster_url }} />
              ))}
            </div>
          )}
          <p className="text-xs text-gray-600 mt-4">
            Recommendations via 3-hop Cypher graph traversal (shared actors + genres).
          </p>
        </div>
      )}
    </div>
  );
}
