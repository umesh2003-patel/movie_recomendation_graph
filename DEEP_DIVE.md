# CineGraph — Architecture & Code Deep Dive

This document provides a detailed breakdown of the codebase to help you understand exactly how the application works. Because the Wexa AI assignment requires you to **explain and defend every part of your submission**, this guide will walk you through the most critical architectural decisions and code blocks.

---

## 1. Database Connection (`backend/database.py`)

This file is responsible for talking to CognoDB using the official `neo4j` Python driver.

```python
def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    return _driver
```
**Why do it this way?**
We use a **Singleton pattern** for the driver. Creating a database driver is an expensive operation (it establishes TCP connections and a connection pool). We only want to create *one* driver for the entire lifespan of the FastAPI application.

```python
@contextmanager
def get_session():
    driver = get_driver()
    session = driver.session()
    try:
        yield session
    finally:
        session.close()
```
**Why do it this way?**
While the *driver* is a singleton, *sessions* are lightweight and not thread-safe. We use Python's `@contextmanager` so that in our API routes, we can use a `with` block:
`with get_session() as session:`
This guarantees that no matter what happens (even if the query crashes), the `finally` block runs and the session is closed, returning the connection to the pool.

---

## 2. API Routing & Cypher Queries (`backend/routers/`)

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

---

## 4. Frontend Application (`frontend/src/`)

### Data Fetching (`api/client.js`)
```javascript
const res = await fetch(`${BASE_URL}${path}`, options);
if (!res.ok) {
  const err = await res.json().catch(() => ({ detail: res.statusText }));
  throw new Error(err.detail || "Request failed");
}
return res.json();
```
We centralized all API calls in `client.js`. If the FastAPI backend returns a `503 Service Unavailable` (e.g., if CognoDB goes offline), this wrapper catches it and throws a standard JavaScript error. This allows our React components to gracefully show the `<ErrorState />` component instead of crashing.

### Parallel Data Loading (`pages/MovieDetail.jsx`)
```javascript
const [m, recs, graph] = await Promise.all([
  api.getMovie(decodedTitle),
  api.recommendForMovie(decodedTitle),
  api.movieGraph(decodedTitle),
]);
```
**Why `Promise.all`?**
When the user opens a movie page, we need three pieces of data: the movie details, the recommendations, and the graph visualizer data. Instead of awaiting them one by one (which would take 3x as long), `Promise.all` fires all three HTTP requests to the backend simultaneously.

### The Graph Visualizer (`components/GraphViewer.jsx`)
We use `react-force-graph-2d`. This library renders using an HTML5 `<canvas>` element rather than standard DOM elements for extreme performance.

```javascript
// Data transformation for the visualizer
graphData={{
  nodes: (data?.nodes || []).map((n) => ({ ...n, id: n.id })),
  links: (data?.links || []).map((l) => ({ source: l.source, target: l.target, label: l.label })),
}}
```
The library expects a strict `{ nodes: [], links: [] }` format. The backend `routers/graph.py` explicitly formats the Cypher output to match this exact shape so the frontend doesn't have to do heavy data processing.

---

## 5. Architectural Defense Summary (For the Interview)

If asked why you built the application this way, highlight these three points:

1. **Graph as a first-class citizen:** We didn't just use CognoDB as a key-value store. We built queries (like the 3-hop recommendation and 2-hop co-actor network) that physically cannot be executed efficiently in SQL.
2. **Resilience & Safety:** Database connections are pooled via a singleton, queries are parameterized against injection, and the frontend degrades gracefully with error boundaries if the database drops.
3. **Performance:** The frontend uses parallel fetching (`Promise.all`), and the graph is rendered using `<canvas>` to ensure 60fps animations even with hundreds of nodes.

