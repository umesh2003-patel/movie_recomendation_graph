import { Link } from "react-router-dom";
import { Film, User } from "lucide-react";

export function ActorCard({ actor }) {
  return (
    <Link
      to={`/actor/${encodeURIComponent(actor.name)}`}
      className="flex items-center gap-3 bg-[#1a1a2e] rounded-xl p-4 border border-gray-800
                 hover:border-[#e94560] transition-all hover:-translate-y-0.5
                 hover:shadow-md hover:shadow-[#e94560]/20"
    >
      <div className="w-10 h-10 rounded-full bg-[#16213e] flex items-center justify-center flex-shrink-0">
        <User size={18} className="text-[#e94560]" />
      </div>
      <div className="min-w-0">
        <p className="text-white font-medium text-sm truncate">{actor.name}</p>
        <div className="flex items-center gap-2 mt-0.5">
          {actor.born && (
            <span className="text-gray-500 text-xs">b. {actor.born}</span>
          )}
          {actor.movie_count != null && (
            <span className="flex items-center gap-1 text-gray-500 text-xs">
              <Film size={10} />
              {actor.movie_count} movies
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
