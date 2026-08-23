import { useParams } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import { MovieCard } from "../components/MovieCard";
import { LoadingState, ErrorState, EmptyState } from "../components/LoadingState";
import { User, Film, Users } from "lucide-react";

export default function ActorDetail() {
  const { name } = useParams();
  const decodedName = decodeURIComponent(name);

  const [actor, setActor] = useState(null);
  const [coActors, setCoActors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [a, co] = await Promise.all([
        api.getActor(decodedName),
        api.coActors(decodedName, 10),
      ]);
      setActor(a);
      setCoActors(co);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [decodedName]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingState message="Loading actor…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!actor) return <EmptyState message="Actor not found." icon="🎭" />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-10">
      {/* Header */}
      <div className="flex items-center gap-6">
        <div className="w-20 h-20 rounded-full bg-[#16213e] flex items-center justify-center flex-shrink-0 border-2 border-[#e94560]">
          <User size={36} className="text-[#e94560]" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-white">{actor.name}</h1>
          {actor.born && <p className="text-gray-400 mt-1">Born: {actor.born}</p>}
          <p className="text-gray-500 text-sm mt-1">
            <Film size={12} className="inline mr-1" />
            {actor.movies?.length} film{actor.movies?.length !== 1 ? "s" : ""}
          </p>
        </div>
      </div>

      {/* Filmography */}
      <section>
        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
          <Film size={18} className="text-[#e94560]" />
          Filmography
        </h2>
        {actor.movies?.length === 0 ? (
          <EmptyState message="No movies found." icon="🎬" />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {actor.movies?.map((m) => (
              <MovieCard key={m.title} movie={m} />
            ))}
          </div>
        )}
      </section>

      {/* Co-actors (2-hop traversal) */}
      <section>
        <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
          <Users size={18} className="text-[#e94560]" />
          Frequent Co-Stars
        </h2>
        <p className="text-gray-500 text-xs mb-6">
          Via 2-hop graph traversal: Actor → Movie ← Actor
        </p>
        {coActors.length === 0 ? (
          <EmptyState message="No co-actor data found." icon="🎭" />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {coActors.map((c) => (
              <div
                key={c.co_actor}
                className="bg-[#1a1a2e] rounded-xl p-4 border border-gray-800"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-medium text-sm">{c.co_actor}</span>
                  <span className="text-xs text-[#e94560] font-bold">
                    {c.shared_movies} shared
                  </span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {c.movies_together?.slice(0, 3).map((t) => (
                    <span key={t} className="text-xs text-gray-500 bg-[#16213e] rounded px-2 py-0.5">
                      {t}
                    </span>
                  ))}
                  {c.movies_together?.length > 3 && (
                    <span className="text-xs text-gray-600">+{c.movies_together.length - 3} more</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
