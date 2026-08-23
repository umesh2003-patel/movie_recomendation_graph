# CineGraph 🎬

> A graph-powered movie exploration and recommendation app backed by **CognoDB** (openCypher / Bolt protocol, Neo4j-compatible).

Built for the **Wexa AI Take-Home Assignment**.

**Status:** ✅ Fully Functional | Ready for Production

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/umesh2003-patel/movie_recomendation_graph.git
cd wexa.ai_project

# Configure environment
cp backend/.env.example .env
# Edit .env with your CognoDB credentials

# Backend
cd backend && pip install -r requirements.txt
python seed.py
uvicorn main:app --reload --port 8000

# Frontend (in another terminal)
cd frontend && npm install && npm run dev
```

Visit `http://localhost:5173` for the app and `http://localhost:8000/docs` for API documentation.

---

## Live Demo

> **Frontend:** [Deploy link here after hosting]
> **API Docs:** [Deploy link]/docs

---

## Why a Graph Database?

Movies, actors, directors, and genres form a naturally connected network. The most interesting questions are about **relationships** — not rows:

| Question | SQL | Cypher |
|----------|-----|--------|
| Who co-starred with Actor X? | 3-table JOIN | 2-hop `MATCH` |
| Recommend movies via shared cast + genre | Nested CTEs | 3-hop MATCH + score formula |
| 6 degrees of Kevin Bacon | Recursive CTE (expensive) | `shortestPath()` (native) |
| All actors reachable in 3 hops | Recursive CTE with depth guard | `ACTED_IN*1..3` |

A graph database **earns its place** here because the data is inherently graph-shaped, and the queries that matter are traversal queries.

---

## Graph Data Model

```
(:Movie {title, year, rating, tagline, poster_url})
(:Actor {name, born})
(:Director {name, born})
(:Genre {name})

(:Actor)-[:ACTED_IN {role}]->(:Movie)
(:Director)-[:DIRECTED]->(:Movie)
(:Movie)-[:IN_GENRE]->(:Genre)
```

### Diagram

```
[Actor] --ACTED_IN {role}--> [Movie] --IN_GENRE--> [Genre]
                                 ^
[Director] ----DIRECTED----------+
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Database | CognoDB (Neo4j / openCypher / Bolt 5.x) |
| Backend | Python + FastAPI |
| Graph Driver | `neo4j` official Python driver |
| Frontend | React + Vite + TailwindCSS |
| Graph Visualiser | react-force-graph-2d |

---

## Project Structure

```
wexa.ai_project/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── database.py          # Driver singleton + error handling
│   ├── seed.py              # Data loader (idempotent MERGE)
│   ├── routers/
│   │   ├── movies.py
│   │   ├── actors.py
│   │   ├── recommendations.py
│   │   └── graph.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/           # Home, MovieDetail, ActorDetail, Explore, Search, Genre
│       ├── components/      # MovieCard, ActorCard, GraphViewer, SearchBar, LoadingState
│       └── api/client.js    # Centralised API client
├── queries/
│   └── cypher_queries.md    # All queries documented
└── .env                     # Never committed (see .env.example)
```

---

## 📋 Setup & Installation

### Prerequisites

- **Python 3.9+** (Backend)
- **Node.js 16+** (Frontend)
- **CognoDB Account** (Free tier available)

### Step 1: Clone and Configure

```bash
git clone https://github.com/umesh2003-patel/movie_recomendation_graph.git
cd wexa.ai_project
cp backend/.env.example .env
```

Edit `.env` with your CognoDB credentials:
```dotenv
CONGODB_CONNECTION_URL=bolt+s://your-instance.bravo.databases.cognodb.com
CONGODB_USERNAME=cognodb
CONGODB_PASSWORD=your-password-here
TMDB_API_KEY=your-tmdb-api-key-optional
```

### Step 2: Create a CognoDB Instance

1. **Sign up** at [console.cognodb.com](https://console.cognodb.com/signup) (free, no credit card required)
2. **Create a free `c0` instance** in your preferred region
3. **Copy credentials:**
   - Connection URI: `bolt+s://...` format
   - Username: `cognodb` (default)
   - Password: Shown once at creation (save it!)
4. **Paste into `.env`**

### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/Scripts/activate  # Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Load seed data into CognoDB
python seed.py

# Start API server
uvicorn main:app --reload --port 8000
```

✅ **API Available at:** http://localhost:8000/docs (interactive Swagger UI)

### Step 4: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ **Frontend Available at:** http://localhost:5173

---

## 📚 API Endpoints

### Movies
- `GET /movies` — List all movies with pagination
- `GET /movies/{title}` — Get movie details by title
- `GET /movies/search?q=query` — Full-text search movies

### Actors
- `GET /actors` — List all actors
- `GET /actors/{name}` — Get actor details
- `GET /actors/{name}/filmography` — Get all movies an actor appeared in
- `GET /actors/{name}/coactors` — Get co-actors (2-hop traversal)

### Recommendations
- `GET /recommendations/movies/{title}` — Get recommendations for a movie (3-hop scoring)
- `GET /recommendations/actors/{name}` — Get actor recommendations based on co-starring patterns

### Graph Visualization
- `GET /graph/movies/{title}` — Get graph data (nodes + links) for movie and connections
- `GET /graph/actors/{name}` — Get graph data centered on an actor

**Full Interactive Docs:** http://localhost:8000/docs (Swagger UI with "Try it out" feature)

---

## 🔍 Key Cypher Queries

See [`queries/cypher_queries.md`](./queries/cypher_queries.md) for complete documentation.

### 2-Hop Co-Actor Traversal
Find all actors who appeared with Actor X:
```cypher
MATCH (a:Actor {name: $name})-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(co:Actor)
WHERE co.name <> $name
RETURN co.name, count(m) AS shared_movies
ORDER BY shared_movies DESC LIMIT 10
```

### 3-Hop Movie Recommendation Engine
Recommend movies based on shared cast + genre:
```cypher
MATCH (m:Movie {title: $title})<-[:ACTED_IN]-(a:Actor)-[:ACTED_IN]->(rec:Movie)
WHERE rec.title <> $title
WITH rec, count(a) AS shared_actors
OPTIONAL MATCH (m:Movie {title: $title})-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(rec)
WITH rec, shared_actors, count(g) AS shared_genres
RETURN rec.title,
       (shared_actors * 2 + shared_genres * 3 + coalesce(rec.rating, 0)) AS score
ORDER BY score DESC LIMIT 6
```

**Scoring:** Shared actors = 2 pts, Shared genres = 3 pts, Movie rating = +baseline

---

## 🌱 Seed Data & Database Schema

### Seed Dataset

The `seed.py` script loads a curated dataset:
- **20 movies** (The Matrix trilogy, Inception, Dark Knight, Pulp Fiction, MCU films, etc.)
- **28 actors** with birth years and biographical data
- **11 directors** with filmography
- **9 genres** (Action, Sci-Fi, Drama, Thriller, etc.)
- **All relationships:** ACTED_IN (with roles), DIRECTED, IN_GENRE

✅ **Idempotent:** All queries use `MERGE` — safe to run `seed.py` multiple times without duplicates.

### Node Properties

**Movie**
```
properties: {title, year, rating, tagline, poster_url}
example: (:Movie {title: "Inception", year: 2010, rating: 8.8})
```

**Actor**
```
properties: {name, born}
example: (:Actor {name: "Leonardo DiCaprio", born: 1974})
```

**Director**
```
properties: {name, born}
example: (:Director {name: "Christopher Nolan", born: 1970})
```

**Genre**
```
properties: {name}
example: (:Genre {name: "Science Fiction"})
```

### Relationship Types

| Relationship | Properties | Direction | Example |
|---|---|---|---|
| `ACTED_IN` | `{role}` | Actor → Movie | `(:Actor)-[:ACTED_IN {role: "Cobb"}]->(:Movie)` |
| `DIRECTED` | None | Director → Movie | `(:Director)-[:DIRECTED]->(:Movie)` |
| `IN_GENRE` | None | Movie → Genre | `(:Movie)-[:IN_GENRE]->(:Genre)` |

### Re-seeding Data

To refresh the database with clean data:
```bash
cd backend
python seed.py  # Drops all nodes/relationships and reloads
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CONGODB_CONNECTION_URL` | Bolt URI from CognoDB console | `bolt+s://db-abc123.bravo.databases.cognodb.com` |
| `CONGODB_USERNAME` | CognoDB username (default) | `cognodb` |
| `CONGODB_PASSWORD` | CognoDB password (keep secret!) | `c7e8e56a92d4929a4294045db93b59d5` |
| `TMDB_API_KEY` | *(Optional)* The Movie Database API key | `8e9ac2af65298ccd01e8bd9eefd82a62` |

> ⚠️ **Security:** Never commit `.env` to the repository. It is listed in `.gitignore`. Treat database credentials as secrets.

### Backend Configuration

**`backend/requirements.txt`** specifies Python dependencies:
- `fastapi` — Web framework
- `neo4j` — CognoDB driver
- `uvicorn` — ASGI server
- `pydantic` — Data validation
- `python-dotenv` — Environment variable loading

### Frontend Configuration

**`frontend/vite.config.js`** and **`frontend/tailwind.config.js`** handle:
- Asset bundling and optimization
- Tailwind CSS styling pipeline
- Development server proxy (if needed)

**API Base URL** is configured in `frontend/src/api/client.js`:
```javascript
const BASE_URL = 'http://localhost:8000';
```

---

## 🎯 Frontend Components

### Pages
- **Home** — Landing page with featured movies and quick links
- **Explore** — Graph visualization interface with node filtering
- **MovieDetail** — Movie info, cast list, recommendations, relationship graph
- **ActorDetail** — Actor profile, filmography, co-actors network
- **Genre** — Browse movies by genre with category filters
- **Search** — Full-text search across movies, actors, and genres

### Reusable Components
- **MovieCard** — Compact movie display with poster, title, rating
- **ActorCard** — Actor profile card with filmography count
- **GraphViewer** — Canvas-based force-directed graph (react-force-graph-2d)
- **SearchBar** — Global search with debouncing
- **LoadingState** — Skeleton screens and spinners
- **ErrorState** — Graceful error boundaries with retry logic

---

## 🔧 Engineering Decisions

### Security & Safety
- **Parameterised Cypher queries everywhere** — zero string concatenation to prevent injection attacks
- **Connection pooling** — Driver singleton pattern for efficient resource management
- **Environment variables** — Credentials never hardcoded

### Resilience
- **Graceful degradation** — API returns HTTP 503 with readable error when database is unreachable
- **Frontend error boundaries** — Components catch errors and display user-friendly error states with retry buttons
- **Session management** — Context managers ensure sessions close even if queries fail

### Performance
- **Parallel data loading** — `Promise.all()` fires multiple API requests simultaneously
- **Canvas-based rendering** — react-force-graph-2d uses HTML5 Canvas for 60fps animations with large graphs
- **Dynamic imports** — Browser-only libraries loaded on-demand to reduce bundle size
- **Query optimization** — Cypher uses `MERGE` for idempotent operations; indexes on title, name

### Maintainability
- **Idempotent seed script** — `MERGE` instead of `CREATE` makes re-runs safe
- **Centralized API client** — All HTTP requests go through `api/client.js` for consistent error handling
- **Documented Cypher queries** — All complex queries explained in `queries/cypher_queries.md`

---

## 📖 Architecture Overview

### Data Flow
```
[Frontend (React)] 
       ↓ HTTP requests
[FastAPI Backend] 
       ↓ Cypher queries (parameterized)
[CognoDB Graph Database]
```

### Connection Lifecycle
```
1. Driver Singleton → Created once, reused for app lifetime
2. Per-Request Session → Lightweight, thread-safe
3. Query Execution → Parameterized, injected as variables
4. Result Streaming → Consumed into Python objects
5. Session Close → Guaranteed via context manager
```

---

## 🛠️ Development

### Running Tests

To test endpoints manually:
```bash
# Interactive API testing
open http://localhost:8000/docs

# Or use curl
curl http://localhost:8000/movies
curl "http://localhost:8000/actors/Leonardo%20DiCaprio"
```

### Database Inspection

Connect directly to CognoDB via console or Cypher shell:
```cypher
MATCH (n) RETURN n LIMIT 10  -- View sample nodes
MATCH ()-[r]->() RETURN type(r), count(r)  -- Relationship summary
```

### Troubleshooting

**Issue:** "Connection refused" error
- ✅ Check `.env` has correct `CONGODB_CONNECTION_URL`
- ✅ Verify CognoDB instance is running in console
- ✅ Confirm network connectivity: `ping db-xyz.bravo.databases.cognodb.com`

**Issue:** "No recommendations found"
- ✅ Ensure `seed.py` has been run successfully
- ✅ Verify movie/actor names match exactly (case-sensitive)
- ✅ Check graph has sufficient data (20+ movies minimum)

**Issue:** Slow graph queries
- ✅ Consider adding indexes on `Movie.title`, `Actor.name`
- ✅ Reduce visualization node limit in `frontend/src/api/client.js`
- ✅ Profile query performance in CognoDB console

---

## 📝 Project Highlights

✨ **Why This Approach?**

1. **Graph Database as First-Class Citizen** — Not using CognoDB as a key-value store. Queries like 3-hop recommendations and shortest-path co-actor networks are **impossible to execute efficiently in SQL**.

2. **Production-Grade Safety** — All queries are parameterized against injection; connections are pooled; error handling is comprehensive with graceful frontend degradation.

3. **Performance-Optimized** — Parallel data fetching, canvas-based rendering, and native graph traversal keep the app responsive even with large datasets.

---

## 📄 License

MIT License — See LICENSE file for details.

---

## 📧 Submission

**Email:** hr@wexa.ai  
**Subject:** `CognoDB Assignment 2 — <Your Name>`

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

**Questions?** Open an issue or reach out to umesh2003-patel.
