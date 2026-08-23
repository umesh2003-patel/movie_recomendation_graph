# CineGraph — Architecture & Code Deep Dive 🔬

This document provides a detailed, line-by-line breakdown of the codebase architecture, design patterns, and critical implementation decisions. This guide is designed to help you:

- Understand **why** each architectural choice was made
- Follow the **data flow** through the entire stack
- **Defend your implementation** in technical interviews
- **Extend the codebase** with confidence

**Target Audience:** Code reviewers, interviewers, and future maintainers.

---

## Table of Contents

1. [Database Connection Pattern](#1-database-connection-pattern)
2. [API Routing & Cypher Queries](#2-api-routing--cypher-queries)
3. [Data Seeding & Idempotency](#3-data-seeding--idempotency)
4. [Frontend Architecture](#4-frontend-architecture)
5. [Error Handling & Resilience](#5-error-handling--resilience)
6. [Performance Optimizations](#6-performance-optimizations)
7. [Security Considerations](#7-security-considerations)
8. [Interview Talking Points](#8-interview-talking-points)

---

## 1. Database Connection Pattern

### File: `backend/database.py`

This module is responsible for managing all communication with CognoDB using the official `neo4j` Python driver.

### 1.1 Driver Singleton

```python
import os
from neo4j import GraphDatabase
from contextlib import contextmanager

URI = os.getenv("CONGODB_CONNECTION_URL")
USERNAME = os.getenv("CONGODB_USERNAME")
PASSWORD = os.getenv("CONGODB_PASSWORD")

_driver = None

def get_driver():
    """Get or create the global graph database driver (Singleton)."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            URI, 
            auth=(USERNAME, PASSWORD),
            encrypted=True  # Enforce TLS for production
        )
    return _driver
```

**Why Singleton?**

Creating a database driver is **expensive**:
- Establishes TCP connections
- Initializes connection pool (typically 50-100 connections)
- Performs authentication handshake
- Sets up protocol negotiation

For a FastAPI application handling many concurrent requests, we want **exactly one driver** that lives for the entire application lifetime. Creating multiple drivers would:
- ❌ Drain system resources (file descriptors, memory)
- ❌ Create unnecessary network connections
- ❌ Slow down request handling

The `global _driver` check ensures lazy initialization — the driver is only created on first use.

### 1.2 Per-Request Session Management

```python
@contextmanager
def get_session():
    """Context manager for thread-safe database sessions.
    
    Guarantees session closure even if the query fails.
    Usage:
        with get_session() as session:
            result = session.run("MATCH (m:Movie) RETURN m LIMIT 10")
    """
    driver = get_driver()
    session = driver.session()
    try:
        yield session
    finally:
        session.close()  # Always runs, even if query raises an exception
```

**Why Sessions Are Different from Drivers:**

| Aspect | Driver | Session |
|--------|--------|---------|
| **Lifetime** | Application-wide singleton | Per-request or per-query |
| **Cost** | Expensive to create | Lightweight, reuses pool |
| **Thread-safe** | ✅ Yes | ❌ No |
| **Pooling** | Contains connection pool | Borrows connection from pool |

**The Context Manager Pattern:**

Python's `@contextmanager` decorator provides a clean way to guarantee cleanup. When we use `with get_session() as session:`, Python guarantees:
1. `session = driver.session()` runs first (the `yield` part)
2. Our code uses the session
3. `session.close()` runs **no matter what** — even if:
   - Query raises an exception
   - User presses Ctrl+C
   - Connection drops
   - Any error occurs

This is equivalent to try/finally but more readable.

**Usage in API Routes:**

```python
@router.get("/movies")
async def list_movies(skip: int = 0, limit: int = 10):
    with get_session() as session:
        result = session.run(
            "MATCH (m:Movie) RETURN m SKIP $skip LIMIT $limit",
            skip=skip, limit=limit
        )
        movies = [record["m"] for record in result]
    return {"movies": movies}  # Session is closed at this point
```

**Connection Pool Benefits:**

CognoDB connections are stateful and expensive. By reusing connections:
- FastAPI can handle 1000s of concurrent requests
- Only actual database resources are used
- Connections are kept alive in the pool, ready for reuse
- Failed connections are automatically replaced

---

## 2. API Routing & Cypher Queries

### File Structure: `backend/routers/`

Each router module maps HTTP endpoints to Cypher queries:

```
routers/
├── movies.py           # GET /movies, /movies/{title}
├── actors.py           # GET /actors, /actors/{name}
├── recommendations.py  # GET /recommendations/*
└── graph.py            # GET /graph/* (visualization data)
```

### 2.1 The 3-Hop Recommendation Engine

**File:** `backend/routers/recommendations.py`

This is the most algorithmically interesting query in the application. Let's break it down line by line.

```cypher
MATCH (m:Movie {title: $title})<-[:ACTED_IN]-(a:Actor)-[:ACTED_IN]->(rec:Movie)
WHERE rec.title <> $title
WITH rec, count(a) AS shared_actors
OPTIONAL MATCH (m:Movie {title: $title})-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(rec)
WITH rec, shared_actors, count(g) AS shared_genres
RETURN rec.title AS title,
       (shared_actors * 2 + shared_genres * 3 + coalesce(rec.rating, 0)) AS score
ORDER BY score DESC LIMIT $limit
```

**Visual Data Flow:**

```
Input: "Inception"
         ↓
    [Inception] --start here
         ↑
         | (backwards) ←ACTED_IN
         |
    [Actor 1: DiCaprio]
    [Actor 2: Marion]
    [Actor 3: Page]
         |
         | (forwards) ACTED_IN→
         ↓
    [The Dark Knight] ← shared 1 actor (DiCaprio)
    [Interstellar]    ← shared 1 actor (Marion)
    [X-Men]           ← shared 2 actors (Page, X)
         ↓
    Score = shared_actors * 2 + shared_genres * 3 + rating
```

**Line-by-Line Explanation:**

**Line 1-2:** Relationship Pattern
```cypher
MATCH (m:Movie {title: $title})<-[:ACTED_IN]-(a:Actor)-[:ACTED_IN]->(rec:Movie)
WHERE rec.title <> $title
```

- `(m:Movie {title: $title})` — Start at the given movie (with parameterized title to prevent injection)
- `<-[:ACTED_IN]-` — Traverse **backwards** along ACTED_IN edges to find all actors in that movie
- `(a:Actor)` — Bind each actor to variable `a`
- `-[:ACTED_IN]->` — Traverse **forwards** from each actor along ACTED_IN edges to find their other movies
- `(rec:Movie)` — Bind each other movie to `rec` ("recommended")
- `WHERE rec.title <> $title` — Exclude the original movie itself from results

This is a **2-hop traversal**: Movie → (backwards) → Actor → (forwards) → Movie

**Line 3:** Aggregation Step
```cypher
WITH rec, count(a) AS shared_actors
```

- `WITH` is a pipeline operator in Cypher — like a checkpoint where we:
  - Discard intermediate variables (like `m` and `a`)
  - Pass forward `rec` and create new variable `shared_actors`
- `count(a)` groups all results by `rec` and counts how many actors connect the original movie to this recommendation
- **Example:** If 3 different actors from "Inception" appeared in "Dark Knight", `shared_actors = 3`

**Line 4-5:** Optional Genre Matching
```cypher
OPTIONAL MATCH (m:Movie {title: $title})-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(rec)
WITH rec, shared_actors, count(g) AS shared_genres
```

- `OPTIONAL MATCH` is crucial here — it means:
  - Try to find matching genres
  - If none exist, still return the row with `g = null`
  - Don't filter out recommendations without shared genres
- This finds genres both movies share (e.g., both are "Action" or "Sci-Fi")
- `count(g)` counts shared genres for each recommendation

**Without `OPTIONAL`:**
- Movies with no genre overlap would be filtered out entirely
- Recommendations would be biased toward exact genre matches

**With `OPTIONAL`:**
- All recommendations are considered
- Movies with 0 shared genres get `shared_genres = 0`
- Scoring still works: `0 * 3 = 0` (no bonus, but not penalized)

**Line 6-7:** Scoring Function
```cypher
RETURN rec.title AS title,
       (shared_actors * 2 + shared_genres * 3 + coalesce(rec.rating, 0)) AS score
```

We calculate a composite score:
- `shared_actors * 2` — Shared cast is worth 2 points per actor
- `shared_genres * 3` — Shared genres are worth 3 points each
- `coalesce(rec.rating, 0)` — Add the movie's rating as a baseline score
  - `coalesce(value, default)` handles null ratings (treats missing as 0)
- **Why these weights?** They're tuned for the domain:
  - Cast is more predictive than genre (actors have consistent acting styles)
  - Genre is moderately important
  - Movie rating (IMDb score) is a tiebreaker

**Example Calculation:**
- "The Dark Knight" appears with 2 shared actors, 1 shared genre, rating 9.0
- Score = 2*2 + 1*3 + 9.0 = 16.0

**Line 8:** Final Sort
```cypher
ORDER BY score DESC LIMIT $limit
```

- Sort all recommendations by score (highest first)
- Return only top `$limit` results (default 6)

### 2.2 Query Parameterization (Security)

```python
# ✅ CORRECT: Parameterized query (injection-safe)
result = session.run(
    "MATCH (m:Movie {title: $title}) RETURN m",
    title=movie_title  # Passed as variable, not concatenated
)

# ❌ WRONG: String concatenation (vulnerable!)
result = session.run(
    f"MATCH (m:Movie {{title: '{movie_title}'}}) RETURN m"
    # If movie_title = 'A'}); DELETE (n) WHERE 1=1; -- 
    # Query becomes: MATCH (m:Movie {title: 'A'}); DELETE (n) WHERE 1=1; -- }) ...
    # Cypher Injection successful!
)
```

**Every single query in this application uses parameterized variables** (`$param_name`) because:
1. **Security** — Prevents Cypher injection attacks
2. **Performance** — Allows database to cache query execution plans
3. **Type Safety** — Driver automatically serializes/deserializes values

---

## 3. Data Seeding & Idempotency

### File: `backend/seed.py`

The seed script initializes the database with a curated dataset of 20 movies, 28 actors, 11 directors, and 9 genres.

```python
def seed_database():
    with get_session() as session:
        # Clear existing data
        session.run("MATCH (n) DETACH DELETE n")
        
        # Seed genres
        for genre in genres:
            session.run("MERGE (:Genre {name: $name})", name=genre)
        
        # Seed actors
        for actor in actors:
            session.run(
                "MERGE (a:Actor {name: $name}) SET a.born = $born",
                name=actor['name'],
                born=actor['born']
            )
        
        # Seed movies with relationships
        for movie in movies:
            session.run(
                "MERGE (m:Movie {title: $title}) "
                "SET m.year = $year, m.rating = $rating",
                title=movie['title'],
                year=movie['year'],
                rating=movie['rating']
            )
            
            # Create ACTED_IN relationships
            for cast_member in movie['cast']:
                session.run(
                    "MATCH (a:Actor {name: $actor}) "
                    "MATCH (m:Movie {title: $movie}) "
                    "MERGE (a)-[:ACTED_IN {role: $role}]->(m)",
                    actor=cast_member['name'],
                    movie=movie['title'],
                    role=cast_member['role']
                )
```

### 3.1 Why `MERGE` Instead of `CREATE`?

**`CREATE`** — Always creates a new node
```cypher
CREATE (:Genre {name: "Action"})
CREATE (:Genre {name: "Action"})
CREATE (:Genre {name: "Action"})
-- Result: 3 identical Genre nodes (wasteful!)
```

**`MERGE`** — Create if doesn't exist, otherwise update
```cypher
MERGE (:Genre {name: "Action"})
MERGE (:Genre {name: "Action"})
MERGE (:Genre {name: "Action"})
-- Result: 1 Genre node (idempotent!)
```

**Benefits of Idempotency:**
- ✅ `seed.py` can be run 100 times — always same result
- ✅ No duplicate data accumulation
- ✅ Safe in development/testing environments
- ✅ Matches database best practices

### 3.2 Data Validation in Seed

The seed script includes validation:
```python
assert len(movies) > 0, "No movies to seed"
assert len(actors) > 0, "No actors to seed"

# Verify relationships exist
result = session.run(
    "MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) RETURN count(*) AS rel_count"
)
rel_count = result.single()[0]
print(f"✅ Seeded {rel_count} ACTED_IN relationships")
```

This ensures the database is in a known good state before starting the application.

---

## 4. Frontend Architecture

The routers map HTTP requests to database queries. Let's look at the most complex and important file: `recommendations.py`.

### The 3-Hop Recommendation Query
```cypher
MATCH (m:Movie {title: $title})<-[:ACTED_IN]-(a:Actor)-[:ACTED_IN]->(rec:Movie)
WHERE rec.title <> $title
WITH rec, count(a) AS shared_actors
OPTIONAL MATCH (m:Movie {title: $title})-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(rec)
WITH rec, shared_actors, count(g) AS shared_genres
RETURN rec.title AS title,
       (shared_actors * 2 + shared_genres * 3 + coalesce(rec.rating, 0)) AS score
ORDER BY score DESC LIMIT $limit
```

**Line-by-Line Breakdown:**
1. `MATCH (m:Movie...`: We start at the movie the user is looking at. We traverse backwards `<-[:ACTED_IN]-` to find all actors in this movie, and then forwards `-[:ACTED_IN]->` to find all *other* movies those actors were in (`rec`).
2. `WHERE rec.title <> $title`: Don't recommend the movie we started with.
3. `WITH rec, count(a) AS shared_actors`: Group the results by the recommended movie, and count how many actors overlap. The `WITH` clause is like a pipeline step, passing these variables to the next part of the query.
4. `OPTIONAL MATCH ...`: Now, check if the original movie and the recommended movie share any genres. `OPTIONAL` means it won't filter out movies that don't share a genre; it just returns `null` for the genre if there's no match.
5. `WITH rec, shared_actors, count(g) AS shared_genres`: Count the overlapping genres.
6. `RETURN ... score`: We calculate a custom recommendation score. Shared actors are worth 2 points, shared genres are worth 3 points, and we add the movie's baseline rating. `coalesce` handles cases where a movie might not have a rating (treats `null` as `0`).
7. `ORDER BY score DESC`: Sort highest score first.

**Why Parameterization?**
Notice we use `$title` and `$limit`, passing them as variables into `session.run()`. We **never** do string formatting like `f"MATCH (m:Movie {{title: {title}}})"`. This prevents Cypher Injection attacks (similar to SQL injection) and allows the database to cache the query execution plan.

---

## 3. Data Seeding (`backend/seed.py`)

The seed script loads the initial data into the graph.

```python
session.run("MERGE (:Genre {name: $name})", name=genre)
```
**Why `MERGE` instead of `CREATE`?**
`MERGE` is the Cypher equivalent of an "Upsert" (Update or Insert). If a genre named "Action" already exists, it does nothing. If it doesn't exist, it creates it. This makes the `seed.py` script **idempotent** — you can run it 100 times safely without creating duplicate nodes.

### 4.1 Centralized API Client (`frontend/src/api/client.js`)

**Pattern: Single Responsibility for HTTP Communication**

```javascript
const BASE_URL = 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, options);
  
  // Error handling
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  
  return res.json();
}

// All API methods use the same request function
export const api = {
  getMovie: (title) => request(`/movies/${encodeURIComponent(title)}`),
  getActor: (name) => request(`/actors/${encodeURIComponent(name)}`),
  recommendForMovie: (title) => request(`/recommendations/movies/${encodeURIComponent(title)}`),
  movieGraph: (title) => request(`/graph/movies/${encodeURIComponent(title)}`),
};
```

**Why Centralize API Calls?**

1. **Error Handling in One Place** — If backend returns 503 (database down):
   ```javascript
   // Instead of this pattern (repeated in 50 components):
   try { const data = await fetch(...); } catch { showError(); }
   
   // We have consistent handling:
   if (!res.ok) {
     const error = await res.json().catch(() => ({ detail: res.statusText }));
     throw new Error(error.detail);  // Caught by React error boundary
   }
   ```

2. **URL Management** — Change `BASE_URL` once, affects entire app
   - Development: `http://localhost:8000`
   - Production: `https://api.example.com`

3. **Authentication** — Can add headers once for all requests:
   ```javascript
   headers: {
     'Authorization': `Bearer ${token}`,
     'Content-Type': 'application/json'
   }
   ```

4. **Retry Logic** — Implement exponential backoff in one place
   ```javascript
   async function requestWithRetry(path, options, retries = 3) {
     for (let i = 0; i < retries; i++) {
       try {
         return await request(path, options);
       } catch (err) {
         if (i === retries - 1) throw err;
         await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000));
       }
     }
   }
   ```

### 4.2 Parallel Data Loading Pattern

**File:** `frontend/src/pages/MovieDetail.jsx`

```javascript
// ❌ Sequential loading (slow!)
const movie = await api.getMovie(decodedTitle);
const recommendations = await api.recommendForMovie(decodedTitle);
const graphData = await api.movieGraph(decodedTitle);
// Total time = request1 + request2 + request3 (e.g., 3 seconds)

// ✅ Parallel loading (fast!)
const [movie, recommendations, graphData] = await Promise.all([
  api.getMovie(decodedTitle),
  api.recommendForMovie(decodedTitle),
  api.movieGraph(decodedTitle),
]);
// Total time = max(request1, request2, request3) (e.g., 1 second)
```

**`Promise.all()` Behavior:**
- Fires all three requests simultaneously
- Waits for all to complete
- Returns results in same order as input array
- If any request fails, entire Promise.all rejects

**Performance Impact:**
```
Sequential:  |---req1---|---req2---|---req3---| (3s)
Parallel:    |---req1---| (1s)
             |---req2---|
             |---req3---|
```

**Error Handling with `Promise.all`:**
```javascript
try {
  const [movie, recs, graph] = await Promise.all([...]);
  setMovie(movie);
  setRecommendations(recs);
  setGraphData(graph);
} catch (err) {
  // ANY failure → entire UI falls back to <ErrorState />
  setError(err.message);
}
```

If backend is slow or down:
- All three requests fail together
- Error boundary catches it
- User sees friendly "Failed to load movie" message
- Can retry once backend recovers

### 4.3 Graph Visualization (`frontend/src/components/GraphViewer.jsx`)

**Library:** `react-force-graph-2d`

```javascript
import ForceGraph2D from 'react-force-graph-2d';

function GraphViewer({ data }) {
  return (
    <ForceGraph2D
      graphData={{
        nodes: (data?.nodes || []).map(n => ({ ...n, id: n.id })),
        links: (data?.links || []).map(l => ({
          source: l.source,
          target: l.target,
          label: l.label,
        })),
      }}
      nodeAutoColorBy="type"
      onNodeClick={(node) => router.push(`/movies/${node.id}`)}
      linkDirectionalArrowLength={3.5}
      linkDirectionalArrowRelPos={1}
    />
  );
}
```

**Why Canvas Instead of SVG?**

| Aspect | SVG (DOM-based) | Canvas (react-force-graph-2d) |
|--------|---|---|
| **Rendering** | One DOM element per node | Draws all at once |
| **Performance** | Slow (500+ nodes) | 60 FPS (thousands of nodes) |
| **Interactivity** | Easy (DOM events) | Custom (manual) |
| **Memory** | High (DOM tree) | Low |

**Data Transformation:**

The backend (in `routers/graph.py`) explicitly returns graph data in the format this library expects:

```python
# Backend returns:
{
  "nodes": [
    {"id": "Inception", "type": "Movie", "val": 10},
    {"id": "DiCaprio", "type": "Actor", "val": 8},
  ],
  "links": [
    {"source": "Inception", "target": "DiCaprio", "label": "ACTED_IN"},
  ]
}

# Frontend just passes through (minimal processing)
graphData={{
  nodes: data.nodes,
  links: data.links,
}}
```

This keeps processing off the JavaScript thread, reducing UI lag.

### 4.4 React Component Structure

**Pages vs. Components:**

```
pages/         → Route-level components (one per URL)
├── Home       → Landing page
├── MovieDetail → Shows movie + recs + graph
├── ActorDetail → Shows actor + co-actors
└── Genre      → Browse by genre

components/    → Reusable building blocks
├── MovieCard
├── ActorCard
├── GraphViewer
└── LoadingState
```

**Data Flow Pattern:**

```
┌─────────────────────────────────────┐
│ Page (e.g., MovieDetail)            │
│ - Fetches data on mount             │
│ - Manages state (movie, recs, etc)  │
│ - Catches errors                    │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ Components (reusable, stateless)    │
│ - Receive props from parent          │
│ - Render UI                         │
│ - Handle user clicks                │
└─────────────────────────────────────┘
```

**Example Page Structure:**

```javascript
// pages/MovieDetail.jsx
function MovieDetail() {
  const { title } = useParams();
  const [movie, setMovie] = useState(null);
  const [recs, setRecs] = useState([]);
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const loadData = async () => {
      try {
        const [m, r, g] = await Promise.all([
          api.getMovie(title),
          api.recommendForMovie(title),
          api.movieGraph(title),
        ]);
        setMovie(m);
        setRecs(r);
        setGraph(g);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [title]);
  
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  
  return (
    <div>
      <MovieCard movie={movie} />
      <div>Recommendations:</div>
      {recs.map(rec => <MovieCard key={rec.title} movie={rec} />)}
      <GraphViewer data={graph} />
    </div>
  );
}
```

---

## 5. Error Handling & Resilience

### 5.1 Backend Error Handling

**File:** `backend/main.py`

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/movies/{title}")
async def get_movie(title: str):
    try:
        with get_session() as session:
            result = session.run(
                "MATCH (m:Movie {title: $title}) RETURN m",
                title=title
            )
            movie = result.single()
            if movie is None:
                raise HTTPException(status_code=404, detail=f"Movie '{title}' not found")
            return {"movie": dict(movie[0])}
    except Exception as e:
        # Log error (in production)
        logger.error(f"Database error: {e}")
        # Return generic 503 to prevent info leakage
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Please try again later."
        )
```

**Error Codes:**
- `200 OK` — Success
- `400 Bad Request` — Invalid input (e.g., missing required parameter)
- `404 Not Found` — Movie/actor doesn't exist
- `500 Internal Server Error` — Bug in our code
- `503 Service Unavailable` — Database down

### 5.2 Frontend Error Boundaries

**Pattern: Graceful Degradation**

```javascript
// pages/MovieDetail.jsx
if (loading) {
  return (
    <div className="flex justify-center items-center h-screen">
      <Spinner />
    </div>
  );
}

if (error) {
  return (
    <div className="p-4 bg-red-100 text-red-800 rounded">
      <h2>Failed to load movie</h2>
      <p>{error}</p>
      <button onClick={() => window.location.reload()}>
        Retry
      </button>
    </div>
  );
}

return (
  <div>
    {/* Normal render */}
  </div>
);
```

**Why Three States?**

1. **Loading** — Data is being fetched, show spinner
2. **Error** — Something failed, show message + retry button
3. **Success** — Data loaded, show content

This prevents the UI from crashing if the database drops mid-session.

---

## 6. Performance Optimizations

### 6.1 Query Optimization

**Cypher Query Plans:**

CognoDB can explain how it executes a query:
```cypher
EXPLAIN
MATCH (m:Movie {title: "Inception"}) RETURN m
```

Output:
```
Production Info    Description
─────────────────────────────────────────
Filter             {m.title = $title}
  └─ AllNodesScan  (:Movie)
```

This scan is **slow** because it checks every movie node. We can add an index:

```cypher
CREATE INDEX ON :Movie(title)
```

Now the same query uses:
```
IndexSeek         :Movie(title = $title)
```

**Much faster!**

### 6.2 Pagination

**Backend:**
```python
@app.get("/movies")
async def list_movies(skip: int = 0, limit: int = 10):
    with get_session() as session:
        result = session.run(
            "MATCH (m:Movie) RETURN m SKIP $skip LIMIT $limit",
            skip=skip, limit=limit
        )
        return [dict(record["m"]) for record in result]
```

**Frontend:**
```javascript
const [page, setPage] = useState(0);
const movies = await api.getMovies(page * 10, 10);

return (
  <div>
    {movies.map(m => <MovieCard key={m.title} movie={m} />)}
    <button onClick={() => setPage(p => p + 1)}>Next</button>
  </div>
);
```

**Why Pagination?**
- ❌ Loading all 1000000 movies wastes bandwidth
- ✅ Load 10 at a time, user only sees what fits on screen
- ✅ Reduces memory usage on frontend

### 6.3 Caching Strategy

**Browser Cache Headers:**

```python
from fastapi.responses import Response

@app.get("/movies/{title}")
async def get_movie(title: str):
    # ... fetch movie ...
    return Response(
        content=json.dumps(movie),
        headers={"Cache-Control": "public, max-age=3600"}  # Cache 1 hour
    )
```

**Why?** If user visits "Inception" page, leaves, then comes back within 1 hour, browser serves cached response instantly without hitting backend.

---

## 7. Security Considerations

### 7.1 Cypher Injection Prevention

**✅ SAFE (Parameterized):**
```python
session.run(
    "MATCH (m:Movie {title: $title}) RETURN m",
    title=user_input
)
```

**❌ UNSAFE (String Concatenation):**
```python
query = f"MATCH (m:Movie {{title: '{user_input}'}}) RETURN m"
session.run(query)
# If user_input = "A'}) RETURN null; DELETE (all) WHERE 1=1 -- 
# Query becomes: MATCH (m:Movie {title: 'A'}); DELETE (all) WHERE 1=1; -- }) RETURN m
```

**Every query in this codebase uses parameterization.** This is non-negotiable.

### 7.2 Environment Variable Management

```python
# ✅ CORRECT: Load from environment
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file
DATABASE_URL = os.getenv("CONGODB_CONNECTION_URL")
DATABASE_PASSWORD = os.getenv("CONGODB_PASSWORD")
```

**Never:**
- ❌ Hardcode credentials in source code
- ❌ Commit `.env` file to git
- ❌ Log sensitive values
- ❌ Pass credentials in query strings

### 7.3 CORS (Cross-Origin Requests)

**Frontend runs on** `http://localhost:5173`  
**Backend runs on** `http://localhost:8000`

Browser blocks cross-origin requests by default. FastAPI needs to allow it:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Production: your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production:** Only allow your own domain, not `["*"]` (open to everyone).

---

## 8. Interview Talking Points

When discussing this implementation with interviewers, emphasize:

### 8.1 Architecture Decisions

**"Why CognoDB and not SQL?"**
> "Movies, actors, and genres form a naturally connected graph. The most interesting queries (recommendations, co-actor networks, shortest paths) are **relationship traversals**, not row lookups. Graph databases excel at these. SQL would require nested CTEs and expensive joins. CognoDB's native path-finding algorithms make this performant."

**"Why Singleton driver + per-request sessions?"**
> "Drivers are expensive (TCP connections, pool setup). We want one that lives for the app. But sessions aren't thread-safe, so we create a lightweight session per request and guarantee cleanup via context managers. This balances resource efficiency with request isolation."

**"Why parameterized queries everywhere?"**
> "Two reasons: (1) Security — parameterization prevents injection attacks. (2) Performance — the database can cache execution plans. Never concatenate user input into queries."

### 8.2 Performance & Scalability

**"How does the recommendation algorithm scale?"**
> "The 3-hop query uses database-native path traversal, which is optimized in CognoDB. Instead of fetching all actors, movies, genres into Python, the query runs on the database where indexes are used. This scales to millions of nodes efficiently."

**"Why parallel fetching instead of sequential?"**
> "On the movie detail page, we need three pieces of data: movie details, recommendations, and graph. Fetching them sequentially takes 3x as long as fetching in parallel. Promise.all() fires all requests simultaneously, improving UX."

### 8.3 Error Handling

**"What happens if the database goes down?"**
> "Backend raises HTTPException with status 503. Frontend's error boundary catches it and shows a user-friendly error message with a retry button. We degrade gracefully instead of crashing."

**"How do you handle null values in Cypher?"**
> "We use the `coalesce()` function, which returns the first non-null value. For example, `coalesce(rec.rating, 0)` treats missing ratings as 0, allowing the scoring formula to work even if data is incomplete."

### 8.4 Why You Built It This Way

**Testability:**
> "By centralizing API calls in `api/client.js`, we can mock the entire backend for testing. Same with the database layer — the `get_session()` context manager makes it easy to mock in unit tests."

**Maintainability:**
> "Cypher queries are well-documented with line-by-line explanations. Each file has a single responsibility (database.py handles connections, routers handle logic, seed.py handles initialization). This makes it easy for future developers to understand and extend."

**Production Readiness:**
> "The app uses connection pooling, parameterized queries, graceful error handling, and logging. It's structured like a real production system, not a prototype."

