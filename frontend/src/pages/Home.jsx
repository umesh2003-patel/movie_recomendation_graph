import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { SearchBar } from "../components/SearchBar";
import { MovieCard } from "../components/MovieCard";
import { ActorCard } from "../components/ActorCard";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { TrendingUp, Users, Tag } from "lucide-react";

export default function Home() {
  const [topMovies, setTopMovies] = useState([]);
  const [actors, setActors] = useState([]);
  const [genres, setGenres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [movies, acts, gens] = await Promise.all([
        api.topMovies(12),
        api.listActors(8),
        api.genres(),
      ]);
      setTopMovies(movies);
      setActors(acts);
      setGenres(gens);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingState message="Loading CineGraph…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-12">
      {/* Hero */}
      <section className="text-center space-y-6 py-12">
        <div className="inline-block px-3 py-1 bg-[#e94560]/10 border border-[#e94560]/30 rounded-full text-[#e94560] text-xs font-medium mb-2">
          Powered by CognoDB Graph Database
        </div>
        <h1 className="text-5xl font-bold text-white leading-tight">
          Discover Movies Through
          <span className="text-[#e94560]"> Connections</span>
        </h1>
        <p className="text-gray-400 max-w-xl mx-auto text-lg">
          Explore the hidden graph of actors, directors, and films — powered by real graph traversal queries.
        </p>
        <div className="flex justify-center">
          <SearchBar placeholder="Search for a movie or actor…" />
        </div>
      </section>

      {/* Top Rated */}
      <section>
        <div className="flex items-center gap-2 mb-6">
          <TrendingUp size={20} className="text-[#e94560]" />
          <h2 className="text-xl font-bold text-white">Top Rated Movies</h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {topMovies.map((m) => <MovieCard key={m.title} movie={m} />)}
        </div>
      </section>

      {/* Genres */}
      <section>
        <div className="flex items-center gap-2 mb-6">
          <Tag size={20} className="text-[#e94560]" />
          <h2 className="text-xl font-bold text-white">Browse by Genre</h2>
        </div>
        <div className="flex flex-wrap gap-3">
          {genres.map((g) => (
            <Link
              key={g.genre}
              to={`/genre/${encodeURIComponent(g.genre)}`}
              className="px-4 py-2 bg-[#1a1a2e] rounded-full border border-gray-700 text-sm text-gray-300
                         hover:border-[#e94560] hover:text-[#e94560] transition-all"
            >
              {g.genre}
              <span className="ml-2 text-xs text-gray-500">{g.movie_count}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* Top Actors */}
      <section>
        <div className="flex items-center gap-2 mb-6">
          <Users size={20} className="text-[#e94560]" />
          <h2 className="text-xl font-bold text-white">Notable Actors</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {actors.map((a) => <ActorCard key={a.name} actor={a} />)}
        </div>
      </section>
    </div>
  );
}
