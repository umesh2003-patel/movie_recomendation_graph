import { BrowserRouter, Routes, Route, Link, NavLink } from "react-router-dom";
import { Film, Network, Home as HomeIcon } from "lucide-react";

import Home from "./pages/Home";
import MovieDetail from "./pages/MovieDetail";
import ActorDetail from "./pages/ActorDetail";
import Explore from "./pages/Explore";
import Search from "./pages/Search";
import Genre from "./pages/Genre";

function Navbar() {
  const linkClass = ({ isActive }) =>
    `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? "bg-[#e94560]/10 text-[#e94560]"
        : "text-gray-400 hover:text-white"
    }`;

  return (
    <header className="sticky top-0 z-50 bg-[#0d0d0d]/90 backdrop-blur-md border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-white font-bold text-xl">
          <Film size={24} className="text-[#e94560]" />
          <span>Cine<span className="text-[#e94560]">Graph</span></span>
        </Link>
        <nav className="flex items-center gap-1">
          <NavLink to="/" end className={linkClass}>
            <HomeIcon size={14} /> Home
          </NavLink>
          <NavLink to="/explore" className={linkClass}>
            <Network size={14} /> Explore
          </NavLink>
        </nav>
        <div className="hidden sm:block text-xs text-gray-600">
          Powered by CognoDB
        </div>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-gray-800 mt-20 py-8 text-center text-gray-600 text-sm">
      <p>
        CineGraph •{" "}
        <span className="text-[#e94560]">CognoDB</span> Graph Database
      </p>
      <p className="mt-1 text-xs text-gray-700">
        Queries use openCypher via the official Neo4j driver over Bolt protocol
      </p>
    </footer>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-[#0d0d0d]">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/movie/:title" element={<MovieDetail />} />
            <Route path="/actor/:name" element={<ActorDetail />} />
            <Route path="/explore" element={<Explore />} />
            <Route path="/search" element={<Search />} />
            <Route path="/genre/:name" element={<Genre />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
