# Cypher Queries — CineGraph

All queries use **parameterised Cypher** via the official Neo4j Python driver.
No string-concatenated Cypher anywhere in the codebase.

---

## 1. Movie Detail with Cast, Director, Genres

```cypher
MATCH (m:Movie {title: $title})
OPTIONAL MATCH (a:Actor)-[r:ACTED_IN]->(m)
OPTIONAL MATCH (d:Director)-[:DIRECTED]->(m)
OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
RETURN m,
       collect(DISTINCT {name: a.name, role: r.role, born: a.born}) AS cast,
       collect(DISTINCT d.name) AS directors,
       collect(DISTINCT g.name) AS genres
```

**Why graph?** A relational DB would need 4 JOINs across 4 bridge tables to produce this result set.

---

## 2. Co-Actor Network (2-Hop Traversal)

```cypher
MATCH (a:Actor {name: $name})-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(co:Actor)
WHERE co.name <> $name
RETURN co.name AS co_actor, count(m) AS shared_movies,
       collect(m.title) AS movies_together
ORDER BY shared_movies DESC LIMIT $limit
```

**Traversal:** `Actor → ACTED_IN → Movie ← ACTED_IN ← Actor`
**Why graph?** This is a textbook 2-hop traversal. In SQL: `SELECT ... FROM actors a1 JOIN acted_in ai1 ON ... JOIN acted_in ai2 ON ... JOIN actors a2 ON ... WHERE a1.name = $name AND a2.name <> a1.name GROUP BY a2.name`.

---

## 3. Movie Recommendation (3-Hop Multi-Signal)

```cypher
MATCH (m:Movie {title: $title})<-[:ACTED_IN]-(a:Actor)-[:ACTED_IN]->(rec:Movie)
WHERE rec.title <> $title
WITH rec, count(a) AS shared_actors
OPTIONAL MATCH (m:Movie {title: $title})-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(rec)
WITH rec, shared_actors, count(g) AS shared_genres
RETURN rec.title AS title,
       rec.year AS year,
       rec.rating AS rating,
       rec.poster_url AS poster_url,
       shared_actors,
       shared_genres,
       (shared_actors * 2 + shared_genres * 3 + coalesce(rec.rating, 0)) AS score
ORDER BY score DESC LIMIT $limit
```

**Why graph?** Computing a weighted multi-signal similarity score across actor and genre relationships in one pass is trivial in Cypher but would require CTEs + multiple self-joins in SQL.

---

## 4. Shortest Path Between Actors (Kevin Bacon-style)

```cypher
MATCH path = shortestPath(
  (a:Actor {name: $from})-[*]-(b:Actor {name: $to})
)
RETURN path
```

**Why graph?** `shortestPath` is a native graph primitive. Equivalent BFS in SQL requires recursive CTEs — O(N) round-trips for large graphs.

---

## 5. Actor Reachability Network (Variable-Hop)

```cypher
MATCH path = (a:Actor {name: $name})-[:ACTED_IN*1..4]->(m:Movie)<-[:ACTED_IN*1..4]-(other:Actor)
WHERE other.name <> $name
RETURN DISTINCT other.name AS actor, length(path) AS distance
ORDER BY distance ASC LIMIT 20
```

**Why graph?** Variable-depth traversal (`*1..4`) is impossible to express in standard SQL without recursive CTEs with depth tracking.

---

## 6. Genre-Based Filtering

```cypher
MATCH (m:Movie)-[:IN_GENRE]->(g:Genre {name: $genre})
RETURN m.title AS title, m.year AS year,
       m.rating AS rating, m.poster_url AS poster_url
ORDER BY m.rating DESC LIMIT $limit
```

---

## 7. Graph Overview (for Visualiser)

```cypher
MATCH (m:Movie)
WITH m ORDER BY m.rating DESC LIMIT $limit
OPTIONAL MATCH (a:Actor)-[:ACTED_IN]->(m)
WITH m, a LIMIT 200
OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
RETURN
  collect(DISTINCT {id: elementId(m), label: m.title, type: 'Movie', rating: m.rating}) AS movies,
  collect(DISTINCT {id: elementId(a), label: a.name, type: 'Actor'}) AS actors,
  collect(DISTINCT {id: elementId(g), label: g.name, type: 'Genre'}) AS genres,
  collect(DISTINCT {source: elementId(a), target: elementId(m), label: 'ACTED_IN'}) AS acted_in,
  collect(DISTINCT {source: elementId(m), target: elementId(g), label: 'IN_GENRE'}) AS in_genre
```
