import { useSearchParams } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import { MovieCard } from "../components/MovieCard";
import { SearchBar } from "../components/SearchBar";
import { LoadingState, EmptyState, ErrorState } from "../components/LoadingState";

export default function Search() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get("q") || "";
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const doSearch = useCallback(async () => {
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.searchMovies(q);
      setResults(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [q]);

  useEffect(() => { doSearch(); }, [doSearch]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-white">Search Results</h1>
        <SearchBar placeholder="Search movies…" />
        {q && <p className="text-gray-400 text-sm">Showing results for "<strong className="text-white">{q}</strong>"</p>}
      </div>

      {loading && <LoadingState message="Searching…" />}
      {error && <ErrorState message={error} onRetry={doSearch} />}
      {!loading && !error && results.length === 0 && q && (
        <EmptyState message={`No movies found for "${q}"`} />
      )}
      {!loading && !error && results.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {results.map((m) => <MovieCard key={m.title} movie={m} />)}
        </div>
      )}
    </div>
  );
}
