# CineGraph 🎬

> A graph-powered movie exploration and recommendation app backed by **CognoDB** (openCypher / Bolt protocol, Neo4j-compatible).

Built for the **Wexa AI Take-Home Assignment**.

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

## Setup & Run

### 1. Clone and configure

```bash
git clone <repo-url>
cd wexa.ai_project
cp backend/.env.example .env
# Edit .env with your CognoDB credentials
```

### 2. Create a CognoDB instance

1. Go to [console.cognodb.com](https://console.cognodb.com/signup) and sign up (free tier, no credit card)
2. Create a free `c0` instance
3. Copy the `bolt+s://...` URI and password into `.env`

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
python seed.py          # Load movie data into CognoDB
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 4. Frontend

```bash
cd frontend
npm install
npm run dev             # http://localhost:5173
```

---

## Key Queries

See [`queries/cypher_queries.md`](./queries/cypher_queries.md) for full documentation.

**Example — 2-hop co-actor traversal:**
```cypher
MATCH (a:Actor {name: $name})-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(co:Actor)
WHERE co.name <> $name
RETURN co.name, count(m) AS shared_movies
ORDER BY shared_movies DESC LIMIT 10
```

**Example — 3-hop movie recommendation:**
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

---

## Seed Data

The `seed.py` script loads:
- **20 movies** (The Matrix trilogy, Inception, Dark Knight, Pulp Fiction, MCU, etc.)
- **28 actors**
- **11 directors**
- **9 genres**
- All ACTED_IN, DIRECTED, IN_GENRE relationships

All Cypher uses `MERGE` — safe to re-run.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CONGODB_CONNECTION_URL` | `bolt+s://...` URI from CognoDB console |
| `CONGODB_USERNAME` | Always `cognodb` |
| `CONGODB_PASSWORD` | Password shown once at instance creation |

> ⚠️ Never commit `.env` to the repository. See `.gitignore`.

---

## Engineering Decisions

- **Parameterised queries everywhere** — zero string-concatenated Cypher
- **Graceful degradation** — API returns HTTP 503 with a human-readable message when DB is unreachable; frontend shows error state with retry
- **Driver singleton** — one persistent driver, sessions opened per request
- **Idempotent seed** — `MERGE` instead of `CREATE` so re-runs are safe
- **Dynamic import** for react-force-graph-2d (browser-only library)

---

## Deep Dive & Interview Prep

A comprehensive line-by-line explanation of the architecture, database connection patterns, and Cypher queries is available in [`DEEP_DIVE.md`](./DEEP_DIVE.md). This document explains the "why" behind the code (e.g., driver singletons, parameterization, parallel fetching) to help prepare for the technical interview.

---

## Submission

Email: hr@wexa.ai
Subject: `CognoDB Assignment 2 — <Your Name>`
