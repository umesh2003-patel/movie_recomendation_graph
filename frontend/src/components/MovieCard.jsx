import { Link } from "react-router-dom";
import { Star } from "lucide-react";

const FALLBACK = "https://via.placeholder.com/300x450/1a1a2e/e94560?text=No+Poster";

export function MovieCard({ movie }) {
  return (
    <Link
      to={`/movie/${encodeURIComponent(movie.title)}`}
      className="group block bg-[#1a1a2e] rounded-xl overflow-hidden border border-gray-800
                 hover:border-[#e94560] transition-all duration-200 hover:shadow-lg hover:shadow-[#e94560]/20
                 hover:-translate-y-1"
    >
      <div className="relative aspect-[2/3] overflow-hidden">
        <img
          src={movie.poster_url || FALLBACK}
          alt={movie.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          onError={(e) => { e.target.src = FALLBACK; }}
          loading="lazy"
        />
        {movie.rating && (
          <div className="absolute top-2 right-2 flex items-center gap-1 bg-black/70 rounded-full px-2 py-1">
            <Star size={12} className="text-[#f5c518] fill-[#f5c518]" />
            <span className="text-xs font-semibold text-[#f5c518]">
              {movie.rating.toFixed(1)}
            </span>
          </div>
        )}
      </div>
      <div className="p-3">
        <h3 className="font-semibold text-white text-sm line-clamp-2 group-hover:text-[#e94560] transition-colors">
          {movie.title}
        </h3>
        <p className="text-gray-500 text-xs mt-1">{movie.year}</p>
      </div>
    </Link>
  );
}
