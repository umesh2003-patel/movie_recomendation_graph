import { useParams } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import { MovieCard } from "../components/MovieCard";
import { LoadingState, ErrorState, EmptyState } from "../components/LoadingState";
import { Tag } from "lucide-react";

export default function Genre() {
  const { name } = useParams();
  const decodedName = decodeURIComponent(name);
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.moviesByGenre(decodedName, 12);
      setMovies(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [decodedName]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <h1 className="text-3xl font-bold text-white flex items-center gap-3">
        <Tag size={24} className="text-[#e94560]" />
        {decodedName} Movies
      </h1>
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={load} />}
      {!loading && !error && movies.length === 0 && (
        <EmptyState message={`No ${decodedName} movies found.`} />
      )}
      {!loading && !error && movies.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {movies.map((m) => <MovieCard key={m.title} movie={m} />)}
        </div>
      )}
    </div>
  );
}
