import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";

export function SearchBar({ placeholder = "Search movies…", autoFocus = false }) {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    const q = query.trim();
    if (q) navigate(`/search?q=${encodeURIComponent(q)}`);
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-xl">
      <Search
        className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
        size={18}
      />
      <input
        autoFocus={autoFocus}
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-[#1a1a2e] text-white pl-11 pr-4 py-3 rounded-xl border border-gray-700
                   focus:outline-none focus:border-[#e94560] transition-colors placeholder-gray-500"
      />
    </form>
  );
}
