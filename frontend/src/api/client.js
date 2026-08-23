const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  // ── Health ────────────────────────────────────────
  health: () => request("/health"),

  // ── Movies ────────────────────────────────────────
  listMovies: (skip = 0, limit = 20) =>
    request(`/movies/?skip=${skip}&limit=${limit}`),
  searchMovies: (q) => request(`/movies/search?q=${encodeURIComponent(q)}`),
  topMovies: (limit = 10) => request(`/movies/top?limit=${limit}`),
  getMovie: (title) => request(`/movies/${encodeURIComponent(title)}`),

  // ── Actors ────────────────────────────────────────
  listActors: (limit = 30) => request(`/actors/?limit=${limit}`),
  getActor: (name) => request(`/actors/${encodeURIComponent(name)}`),
  coActors: (name, limit = 10) =>
    request(`/actors/${encodeURIComponent(name)}/co-actors?limit=${limit}`),

  // ── Recommendations ───────────────────────────────
  recommendForMovie: (title, limit = 6) =>
    request(`/recommendations/movie/${encodeURIComponent(title)}?limit=${limit}`),
  genres: () => request("/recommendations/genres"),
  moviesByGenre: (genre, limit = 12) =>
    request(`/recommendations/similar-genre/${encodeURIComponent(genre)}?limit=${limit}`),

  // ── Graph ─────────────────────────────────────────
  movieGraph: (title) => request(`/graph/movie/${encodeURIComponent(title)}`),
  graphOverview: (limit = 30) => request(`/graph/overview?limit=${limit}`),
};
